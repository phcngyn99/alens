"""
IBM DB2 database introspector.
Queries DB2 system catalogs for schema metadata.
Uses ibm_db for connectivity.
"""

from typing import Optional

from app.core.introspect.base import BaseIntrospector, ConnectionConfig, DriverStatus
from app.core.models.schema import Column, ForeignKey, Index, PrimaryKey, Table


class DB2Introspector(BaseIntrospector):
    """IBM DB2-specific introspection using ibm_db."""

    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self._connection = None

    @property
    def db_type(self) -> str:
        return "db2"

    @classmethod
    def check_driver(cls) -> DriverStatus:
        """Check if ibm_db is installed."""
        try:
            import ibm_db

            return DriverStatus(
                driver_name="ibm_db",
                is_installed=True,
                version=(
                    ibm_db.__version__ if hasattr(ibm_db, "__version__") else "unknown"
                ),
            )
        except ImportError:
            return DriverStatus(
                driver_name="ibm_db",
                is_installed=False,
                install_instructions="pip install ibm-db",
            )

    def _get_connection_string(self) -> str:
        """Build DB2 connection string."""
        return (
            f"DATABASE={self.config.database};"
            f"HOSTNAME={self.config.host};"
            f"PORT={self.config.port};"
            f"PROTOCOL=TCPIP;"
            f"UID={self.config.username};"
            f"PWD={self.config.password};"
        )

    async def connect(self) -> bool:
        """Connect to DB2 database."""
        try:
            import ibm_db

            self._connection = ibm_db.connect(self._get_connection_string(), "", "")
            return True
        except Exception:
            return False

    async def disconnect(self) -> None:
        """Close the connection."""
        if self._connection:
            import ibm_db

            ibm_db.close(self._connection)
            self._connection = None

    async def test_connection(self) -> tuple[bool, str]:
        """Test the database connection."""
        try:
            import ibm_db

            if not self._connection:
                await self.connect()
            stmt = ibm_db.exec_immediate(
                self._connection, "SELECT SERVICE_LEVEL FROM SYSIBMADM.ENV_INST_INFO"
            )
            result = ibm_db.fetch_tuple(stmt)
            return True, f"Connected: DB2 {result[0] if result else 'unknown'}"
        except Exception as e:
            return False, str(e)

    async def get_schemas(self) -> list[str]:
        """Get list of schemas."""
        import ibm_db

        query = """
            SELECT SCHEMANAME FROM SYSCAT.SCHEMATA 
            WHERE SCHEMANAME NOT LIKE 'SYS%' AND SCHEMANAME NOT LIKE 'NULL%'
            ORDER BY SCHEMANAME
        """
        stmt = ibm_db.exec_immediate(self._connection, query)
        schemas = []
        while row := ibm_db.fetch_tuple(stmt):
            schemas.append(row[0].strip())

        if self.config.schema_whitelist:
            schemas = [s for s in schemas if s in self.config.schema_whitelist]

        return schemas

    async def get_tables(self, schema_name: str) -> list[str]:
        """Get list of tables in a schema."""
        import ibm_db

        query = f"""
            SELECT TABNAME FROM SYSCAT.TABLES 
            WHERE TABSCHEMA = '{schema_name}' AND TYPE = 'T'
            ORDER BY TABNAME
        """
        stmt = ibm_db.exec_immediate(self._connection, query)
        tables = []
        while row := ibm_db.fetch_tuple(stmt):
            tables.append(row[0].strip())
        return tables

    async def introspect_table(self, schema_name: str, table_name: str) -> Table:
        """Fully introspect a DB2 table."""
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

        timestamp_types = {"timestamp", "date", "time"}
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
        import ibm_db

        query = f"""
            SELECT COLNAME, TYPENAME, NULLS, DEFAULT
            FROM SYSCAT.COLUMNS
            WHERE TABSCHEMA = '{schema_name}' AND TABNAME = '{table_name}'
            ORDER BY COLNO
        """
        stmt = ibm_db.exec_immediate(self._connection, query)
        columns = []
        while row := ibm_db.fetch_tuple(stmt):
            columns.append(
                Column(
                    name=row[0].strip(),
                    data_type=row[1].strip(),
                    nullable=row[2] == "Y",
                    default_value=row[3].strip() if row[3] else None,
                )
            )
        return columns

    async def _get_primary_key(
        self, schema_name: str, table_name: str
    ) -> Optional[PrimaryKey]:
        """Get primary key constraint."""
        import ibm_db

        query = f"""
            SELECT CONSTNAME, COLNAME
            FROM SYSCAT.KEYCOLUSE
            WHERE TABSCHEMA = '{schema_name}' AND TABNAME = '{table_name}'
            ORDER BY COLSEQ
        """
        stmt = ibm_db.exec_immediate(self._connection, query)
        rows = []
        while row := ibm_db.fetch_tuple(stmt):
            rows.append(row)
        if rows:
            return PrimaryKey(
                name=rows[0][0].strip(), columns=[r[1].strip() for r in rows]
            )
        return None

    async def _get_foreign_keys(
        self, schema_name: str, table_name: str
    ) -> list[ForeignKey]:
        """Get foreign key constraints."""
        import ibm_db

        query = f"""
            SELECT CONSTNAME, FK_COLNAMES, REFTABSCHEMA, REFTABNAME, PK_COLNAMES
            FROM SYSCAT.REFERENCES
            WHERE TABSCHEMA = '{schema_name}' AND TABNAME = '{table_name}'
        """
        stmt = ibm_db.exec_immediate(self._connection, query)
        fks = []
        while row := ibm_db.fetch_tuple(stmt):
            fks.append(
                ForeignKey(
                    name=row[0].strip(),
                    columns=[c.strip() for c in row[1].split()],
                    referenced_schema=row[2].strip(),
                    referenced_table=row[3].strip(),
                    referenced_columns=[c.strip() for c in row[4].split()],
                )
            )
        return fks

    async def _get_indexes(self, schema_name: str, table_name: str) -> list[Index]:
        """Get index information."""
        import ibm_db

        query = f"""
            SELECT INDNAME, COLNAMES, UNIQUERULE
            FROM SYSCAT.INDEXES
            WHERE TABSCHEMA = '{schema_name}' AND TABNAME = '{table_name}'
        """
        stmt = ibm_db.exec_immediate(self._connection, query)
        indexes = []
        while row := ibm_db.fetch_tuple(stmt):
            # COLNAMES format: +COL1+COL2 or -COL1-COL2 (+ asc, - desc)
            cols = [c.strip().lstrip("+-") for c in row[1].split() if c.strip()]
            indexes.append(
                Index(
                    name=row[0].strip(),
                    columns=cols,
                    is_unique=row[2] in ("U", "P"),
                    is_primary=row[2] == "P",
                )
            )
        return indexes

    async def get_sample_data(
        self, schema_name: str, table_name: str, limit: int = 20
    ) -> tuple[list[str], list[list]]:
        """Get sample data from a DB2 table."""
        import ibm_db

        # First get column names
        columns_query = f"""
            SELECT COLNAME
            FROM SYSCAT.COLUMNS
            WHERE TABSCHEMA = '{schema_name}' AND TABNAME = '{table_name}'
            ORDER BY COLNO
        """
        stmt = ibm_db.exec_immediate(self._connection, columns_query)
        column_names = []
        while row := ibm_db.fetch_tuple(stmt):
            column_names.append(row[0].strip())

        if not column_names:
            return [], []

        # Fetch sample data
        data_query = f"""
            SELECT * FROM "{schema_name}"."{table_name}"
            FETCH FIRST {int(limit)} ROWS ONLY
        """
        stmt = ibm_db.exec_immediate(self._connection, data_query)

        # Convert rows to list of lists
        data = []
        while row := ibm_db.fetch_tuple(stmt):
            row_data = []
            for val in row:
                if val is None:
                    row_data.append(None)
                elif isinstance(val, (str, int, float, bool)):
                    # Strip whitespace from strings
                    row_data.append(val.strip() if isinstance(val, str) else val)
                else:
                    row_data.append(str(val))
            data.append(row_data)

        return column_names, data
