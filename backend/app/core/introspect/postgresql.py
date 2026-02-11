"""
PostgreSQL database introspector.
Queries PostgreSQL system catalogs for schema metadata.
"""

from typing import Optional

import asyncpg

from app.core.introspect.base import BaseIntrospector, ConnectionConfig, DriverStatus
from app.core.models.schema import Column, ForeignKey, Index, PrimaryKey, Table


class PostgreSQLIntrospector(BaseIntrospector):
    """PostgreSQL-specific introspection using asyncpg."""

    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self._connection: Optional[asyncpg.Connection] = None

    @property
    def db_type(self) -> str:
        return "postgresql"

    @classmethod
    def check_driver(cls) -> DriverStatus:
        """Check if asyncpg is installed."""
        try:
            import asyncpg

            return DriverStatus(
                driver_name="asyncpg",
                is_installed=True,
                version=asyncpg.__version__,
            )
        except ImportError:
            return DriverStatus(
                driver_name="asyncpg",
                is_installed=False,
                install_instructions="pip install asyncpg",
            )

    async def connect(self) -> bool:
        """Connect to PostgreSQL database."""
        try:
            self._connection = await asyncpg.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                timeout=10,
            )
            return True
        except Exception as e:
            self._last_error = str(e)
            return False

    async def disconnect(self) -> None:
        """Close the connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def test_connection(self) -> tuple[bool, str]:
        """Test the database connection."""
        try:
            if not self._connection:
                await self.connect()
            result = await self._connection.fetchval("SELECT version()")
            return True, f"Connected: {result[:50]}..."
        except Exception as e:
            return False, str(e)

    async def get_schemas(self) -> list[str]:
        """Get list of schemas, respecting whitelist."""
        query = """
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name
        """
        rows = await self._connection.fetch(query)
        schemas = [row["schema_name"] for row in rows]

        if self.config.schema_whitelist:
            schemas = [s for s in schemas if s in self.config.schema_whitelist]

        return schemas

    async def get_tables(self, schema_name: str) -> list[str]:
        """Get list of tables in a schema."""
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = $1 AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        rows = await self._connection.fetch(query, schema_name)
        return [row["table_name"] for row in rows]

    async def introspect_table(self, schema_name: str, table_name: str) -> Table:
        """Fully introspect a PostgreSQL table."""
        columns = await self._get_columns(schema_name, table_name)
        primary_key = await self._get_primary_key(schema_name, table_name)
        foreign_keys = await self._get_foreign_keys(schema_name, table_name)
        indexes = await self._get_indexes(schema_name, table_name)

        # Mark PK/FK columns
        pk_cols = set(primary_key.columns) if primary_key else set()
        fk_cols = set()
        for fk in foreign_keys:
            fk_cols.update(fk.columns)

        for col in columns:
            col.is_primary_key = col.name in pk_cols
            col.is_foreign_key = col.name in fk_cols

        # Detect timestamp columns
        timestamp_types = {
            "timestamp",
            "timestamptz",
            "date",
            "timestamp without time zone",
            "timestamp with time zone",
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
            SELECT column_name, data_type, is_nullable, column_default,
                   col_description((table_schema || '.' || table_name)::regclass, ordinal_position) as comment
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
        """
        rows = await self._connection.fetch(query, schema_name, table_name)
        return [
            Column(
                name=row["column_name"],
                data_type=row["data_type"],
                nullable=row["is_nullable"] == "YES",
                default_value=row["column_default"],
                comment=row["comment"],
            )
            for row in rows
        ]

    async def _get_primary_key(
        self, schema_name: str, table_name: str
    ) -> Optional[PrimaryKey]:
        """Get primary key constraint."""
        query = """
            SELECT c.conname, array_agg(a.attname ORDER BY array_position(c.conkey, a.attnum)) as columns
            FROM pg_constraint c
            JOIN pg_class t ON t.oid = c.conrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(c.conkey)
            WHERE n.nspname = $1 AND t.relname = $2 AND c.contype = 'p'
            GROUP BY c.conname
        """
        row = await self._connection.fetchrow(query, schema_name, table_name)
        if row:
            return PrimaryKey(name=row["conname"], columns=list(row["columns"]))
        return None

    async def _get_foreign_keys(
        self, schema_name: str, table_name: str
    ) -> list[ForeignKey]:
        """Get foreign key constraints."""
        query = """
            SELECT
                c.conname,
                array_agg(a.attname ORDER BY array_position(c.conkey, a.attnum)) as columns,
                rn.nspname as ref_schema,
                rt.relname as ref_table,
                array_agg(ra.attname ORDER BY array_position(c.confkey, ra.attnum)) as ref_columns
            FROM pg_constraint c
            JOIN pg_class t ON t.oid = c.conrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(c.conkey)
            JOIN pg_class rt ON rt.oid = c.confrelid
            JOIN pg_namespace rn ON rn.oid = rt.relnamespace
            JOIN pg_attribute ra ON ra.attrelid = rt.oid AND ra.attnum = ANY(c.confkey)
            WHERE n.nspname = $1 AND t.relname = $2 AND c.contype = 'f'
            GROUP BY c.conname, rn.nspname, rt.relname
        """
        rows = await self._connection.fetch(query, schema_name, table_name)
        return [
            ForeignKey(
                name=row["conname"],
                columns=list(row["columns"]),
                referenced_schema=row["ref_schema"],
                referenced_table=row["ref_table"],
                referenced_columns=list(row["ref_columns"]),
            )
            for row in rows
        ]

    async def _get_indexes(self, schema_name: str, table_name: str) -> list[Index]:
        """Get index information."""
        query = """
            SELECT
                i.relname as index_name,
                array_agg(a.attname ORDER BY array_position(ix.indkey, a.attnum)) as columns,
                ix.indisunique as is_unique,
                ix.indisprimary as is_primary
            FROM pg_index ix
            JOIN pg_class t ON t.oid = ix.indrelid
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
            WHERE n.nspname = $1 AND t.relname = $2
            GROUP BY i.relname, ix.indisunique, ix.indisprimary
        """
        rows = await self._connection.fetch(query, schema_name, table_name)
        return [
            Index(
                name=row["index_name"],
                columns=list(row["columns"]),
                is_unique=row["is_unique"],
                is_primary=row["is_primary"],
            )
            for row in rows
        ]

    async def get_approximate_row_count(
        self, schema_name: str, table_name: str
    ) -> Optional[int]:
        """Get approximate row count from pg_stat_user_tables."""
        query = """
            SELECT n_live_tup
            FROM pg_stat_user_tables
            WHERE schemaname = $1 AND relname = $2
        """
        row = await self._connection.fetchrow(query, schema_name, table_name)
        return row["n_live_tup"] if row else None

    async def get_sample_data(
        self, schema_name: str, table_name: str, limit: int = 20
    ) -> tuple[list[str], list[list]]:
        """Get sample data from a PostgreSQL table."""
        # First get column names
        columns_query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
        """
        col_rows = await self._connection.fetch(columns_query, schema_name, table_name)
        column_names = [row["column_name"] for row in col_rows]

        if not column_names:
            return [], []

        # Fetch sample data - use identifier quoting to prevent SQL injection
        # asyncpg doesn't support parameterized identifiers, so we validate them
        safe_schema = schema_name.replace('"', '""')
        safe_table = table_name.replace('"', '""')
        data_query = f'SELECT * FROM "{safe_schema}"."{safe_table}" LIMIT {int(limit)}'

        rows = await self._connection.fetch(data_query)

        # Convert rows to list of lists, handling special types
        data = []
        for row in rows:
            row_data = []
            for col in column_names:
                val = row.get(col)
                # Convert non-JSON-serializable types to strings
                if val is None:
                    row_data.append(None)
                elif isinstance(val, (str, int, float, bool)):
                    row_data.append(val)
                else:
                    row_data.append(str(val))
            data.append(row_data)

        return column_names, data
