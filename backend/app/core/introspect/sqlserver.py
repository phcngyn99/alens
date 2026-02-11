"""
SQL Server database introspector.
Queries SQL Server system catalogs for schema metadata.
Uses pyodbc for connectivity.
"""

from typing import Optional

from app.core.introspect.base import BaseIntrospector, ConnectionConfig, DriverStatus
from app.core.models.schema import Column, ForeignKey, Index, PrimaryKey, Table


class SQLServerIntrospector(BaseIntrospector):
    """SQL Server-specific introspection using pyodbc."""

    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self._connection = None
        self._cursor = None

    @property
    def db_type(self) -> str:
        return "sqlserver"

    @classmethod
    def check_driver(cls) -> DriverStatus:
        """Check if pyodbc is installed."""
        try:
            import pyodbc

            return DriverStatus(
                driver_name="pyodbc",
                is_installed=True,
                version=pyodbc.version,
            )
        except ImportError:
            return DriverStatus(
                driver_name="pyodbc",
                is_installed=False,
                install_instructions="pip install pyodbc",
            )

    def _get_connection_string(self) -> str:
        """Build ODBC connection string."""
        # Try common SQL Server ODBC drivers
        drivers = [
            "ODBC Driver 18 for SQL Server",
            "ODBC Driver 17 for SQL Server",
            "SQL Server Native Client 11.0",
            "SQL Server",
        ]
        driver = drivers[0]  # Default to latest

        return (
            f"DRIVER={{{driver}}};"
            f"SERVER={self.config.host},{self.config.port};"
            f"DATABASE={self.config.database};"
            f"UID={self.config.username};"
            f"PWD={self.config.password};"
            "TrustServerCertificate=yes;"
        )

    async def connect(self) -> bool:
        """Connect to SQL Server database."""
        try:
            import pyodbc

            # pyodbc is synchronous, but we wrap it for consistency
            self._connection = pyodbc.connect(self._get_connection_string(), timeout=10)
            self._cursor = self._connection.cursor()
            return True
        except Exception as e:
            self._last_error = str(e)
            return False

    def get_last_error(self) -> str:
        """Get the last connection error message."""
        return getattr(self, "_last_error", "Unknown error")

    async def disconnect(self) -> None:
        """Close the connection."""
        if self._cursor:
            self._cursor.close()
        if self._connection:
            self._connection.close()
        self._connection = None
        self._cursor = None

    async def test_connection(self) -> tuple[bool, str]:
        """Test the database connection."""
        try:
            if not self._connection:
                await self.connect()
            self._cursor.execute("SELECT @@VERSION")
            result = self._cursor.fetchone()[0]
            return True, f"Connected: {result[:50]}..."
        except Exception as e:
            return False, str(e)

    async def get_schemas(self) -> list[str]:
        """Get list of schemas."""
        query = """
            SELECT SCHEMA_NAME 
            FROM INFORMATION_SCHEMA.SCHEMATA 
            WHERE SCHEMA_NAME NOT IN ('sys', 'INFORMATION_SCHEMA', 'guest')
            ORDER BY SCHEMA_NAME
        """
        self._cursor.execute(query)
        schemas = [row[0] for row in self._cursor.fetchall()]

        if self.config.schema_whitelist:
            schemas = [s for s in schemas if s in self.config.schema_whitelist]

        return schemas

    async def get_tables(self, schema_name: str) -> list[str]:
        """Get list of tables in a schema."""
        query = """
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = ? AND TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """
        self._cursor.execute(query, schema_name)
        return [row[0] for row in self._cursor.fetchall()]

    async def introspect_table(self, schema_name: str, table_name: str) -> Table:
        """Fully introspect a SQL Server table."""
        columns = await self._get_columns(schema_name, table_name)
        primary_key = await self._get_primary_key(schema_name, table_name)
        foreign_keys = await self._get_foreign_keys(schema_name, table_name)
        indexes = await self._get_indexes(schema_name, table_name)

        pk_cols = set(primary_key.columns) if primary_key else set()
        fk_cols = set()
        for fk in foreign_keys:
            fk_cols.update(fk.columns)

        for col in columns:
            col.is_primary_key = col.name in pk_cols
            col.is_foreign_key = col.name in fk_cols

        timestamp_types = {
            "datetime",
            "datetime2",
            "date",
            "smalldatetime",
            "datetimeoffset",
        }
        has_timestamps = any(
            col.data_type.lower() in timestamp_types for col in columns
        )

        return Table(
            schema_name=schema_name,
            name=table_name,
            columns=columns,
            primary_key=primary_key,
            foreign_keys=foreign_keys,
            indexes=indexes,
            has_timestamp_columns=has_timestamps,
            fk_count=len(foreign_keys),
        )

    async def _get_columns(self, schema_name: str, table_name: str) -> list[Column]:
        """Get column information."""
        query = """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
        """
        self._cursor.execute(query, schema_name, table_name)
        return [
            Column(
                name=row[0],
                data_type=row[1],
                nullable=row[2] == "YES",
                default_value=row[3],
            )
            for row in self._cursor.fetchall()
        ]

    async def _get_primary_key(
        self, schema_name: str, table_name: str
    ) -> Optional[PrimaryKey]:
        """Get primary key constraint."""
        query = """
            SELECT kc.CONSTRAINT_NAME, kc.COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE kc
            JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                ON kc.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
            WHERE tc.TABLE_SCHEMA = ? AND tc.TABLE_NAME = ? AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
            ORDER BY kc.ORDINAL_POSITION
        """
        self._cursor.execute(query, schema_name, table_name)
        rows = self._cursor.fetchall()
        if rows:
            return PrimaryKey(name=rows[0][0], columns=[row[1] for row in rows])
        return None

    async def _get_foreign_keys(
        self, schema_name: str, table_name: str
    ) -> list[ForeignKey]:
        """Get foreign key constraints."""
        query = """
            SELECT
                fk.name AS constraint_name,
                COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS column_name,
                SCHEMA_NAME(rt.schema_id) AS ref_schema,
                rt.name AS ref_table,
                COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS ref_column
            FROM sys.foreign_keys fk
            JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
            JOIN sys.tables t ON fk.parent_object_id = t.object_id
            JOIN sys.tables rt ON fk.referenced_object_id = rt.object_id
            WHERE SCHEMA_NAME(t.schema_id) = ? AND t.name = ?
            ORDER BY fk.name, fkc.constraint_column_id
        """
        self._cursor.execute(query, schema_name, table_name)
        rows = self._cursor.fetchall()

        fk_dict = {}
        for row in rows:
            name = row[0]
            if name not in fk_dict:
                fk_dict[name] = ForeignKey(
                    name=name,
                    columns=[],
                    referenced_schema=row[2],
                    referenced_table=row[3],
                    referenced_columns=[],
                )
            fk_dict[name].columns.append(row[1])
            fk_dict[name].referenced_columns.append(row[4])

        return list(fk_dict.values())

    async def _get_indexes(self, schema_name: str, table_name: str) -> list[Index]:
        """Get index information."""
        query = """
            SELECT i.name, c.name, i.is_unique, i.is_primary_key
            FROM sys.indexes i
            JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            JOIN sys.tables t ON i.object_id = t.object_id
            WHERE SCHEMA_NAME(t.schema_id) = ? AND t.name = ? AND i.name IS NOT NULL
            ORDER BY i.name, ic.key_ordinal
        """
        self._cursor.execute(query, schema_name, table_name)
        rows = self._cursor.fetchall()

        idx_dict = {}
        for row in rows:
            name = row[0]
            if name not in idx_dict:
                idx_dict[name] = Index(
                    name=name, columns=[], is_unique=row[2], is_primary=row[3]
                )
            idx_dict[name].columns.append(row[1])

        return list(idx_dict.values())

    async def get_sample_data(
        self, schema_name: str, table_name: str, limit: int = 20
    ) -> tuple[list[str], list[list]]:
        """Get sample data from a SQL Server table."""
        # First get column names
        columns_query = """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
        """
        self._cursor.execute(columns_query, schema_name, table_name)
        column_names = [row[0] for row in self._cursor.fetchall()]

        if not column_names:
            return [], []

        # Fetch sample data - use bracket quoting for identifiers
        safe_schema = schema_name.replace("]", "]]")
        safe_table = table_name.replace("]", "]]")
        data_query = f"SELECT TOP {int(limit)} * FROM [{safe_schema}].[{safe_table}]"

        self._cursor.execute(data_query)
        rows = self._cursor.fetchall()

        # Convert rows to list of lists, handling special types
        data = []
        for row in rows:
            row_data = []
            for val in row:
                if val is None:
                    row_data.append(None)
                elif isinstance(val, (str, int, float, bool)):
                    row_data.append(val)
                else:
                    row_data.append(str(val))
            data.append(row_data)

        return column_names, data
