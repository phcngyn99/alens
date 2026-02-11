"""
Statistics collector for database tables.
Collects optional statistics that are clearly labeled as "observed, not guaranteed".

Statistics collected:
- Approximate row count
- Distinct count per column
- Null ratio per column
- Min/max for date and numeric columns
"""
from dataclasses import dataclass
from typing import Optional

from app.core.introspect.base import BaseIntrospector
from app.core.models.schema import Column, Table


@dataclass
class ColumnStats:
    """Statistics for a single column."""
    column_name: str
    distinct_count: Optional[int] = None
    null_count: Optional[int] = None
    null_ratio: Optional[float] = None
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    
    # Metadata
    is_observed: bool = True  # Always true - these are observed stats


@dataclass
class TableStats:
    """Statistics for a table."""
    table_name: str
    schema_name: str
    approximate_row_count: Optional[int] = None
    column_stats: dict[str, ColumnStats] = None
    
    # Warning label
    disclaimer: str = "Statistics are observed values, not guaranteed. They may be stale or approximate."
    
    def __post_init__(self):
        if self.column_stats is None:
            self.column_stats = {}


class StatsCollector:
    """
    Collects statistics from database tables.
    
    All statistics are READ-ONLY operations.
    Statistics are clearly labeled as observed/approximate.
    """
    
    def __init__(self, introspector: BaseIntrospector):
        self.introspector = introspector
    
    async def collect_table_stats(
        self,
        schema_name: str,
        table_name: str,
        include_column_stats: bool = True,
        sample_size: int = 10000,
    ) -> TableStats:
        """
        Collect statistics for a table.
        
        Args:
            schema_name: Schema name
            table_name: Table name
            include_column_stats: Whether to collect per-column statistics
            sample_size: Maximum rows to sample for statistics (for performance)
            
        Returns:
            TableStats with observed statistics
        """
        stats = TableStats(table_name=table_name, schema_name=schema_name)
        
        # Get approximate row count (database-specific)
        if hasattr(self.introspector, 'get_approximate_row_count'):
            stats.approximate_row_count = await self.introspector.get_approximate_row_count(
                schema_name, table_name
            )
        
        if include_column_stats:
            # Get table metadata to know column types
            table = await self.introspector.introspect_table(schema_name, table_name)
            
            for column in table.columns:
                col_stats = await self._collect_column_stats(
                    schema_name, table_name, column, sample_size
                )
                stats.column_stats[column.name] = col_stats
        
        return stats
    
    async def _collect_column_stats(
        self,
        schema_name: str,
        table_name: str,
        column: Column,
        sample_size: int,
    ) -> ColumnStats:
        """
        Collect statistics for a single column.
        Uses database-specific queries for efficiency.
        """
        col_stats = ColumnStats(column_name=column.name)
        
        # Build statistics query based on database type
        # This is a simplified version - each introspector could have optimized queries
        db_type = self.introspector.db_type
        full_table = f"{schema_name}.{table_name}"
        col_name = column.name
        
        if db_type == "postgresql":
            await self._collect_postgres_stats(full_table, col_name, column, col_stats)
        elif db_type == "sqlserver":
            await self._collect_sqlserver_stats(full_table, col_name, column, col_stats)
        elif db_type == "db2":
            await self._collect_db2_stats(full_table, col_name, column, col_stats)
        
        return col_stats
    
    async def _collect_postgres_stats(
        self, full_table: str, col_name: str, column: Column, stats: ColumnStats
    ) -> None:
        """Collect statistics using PostgreSQL-specific queries."""
        conn = self.introspector._connection
        
        # Distinct count and null count
        query = f"""
            SELECT 
                COUNT(DISTINCT "{col_name}") as distinct_count,
                COUNT(*) FILTER (WHERE "{col_name}" IS NULL) as null_count,
                COUNT(*) as total_count
            FROM {full_table}
        """
        row = await conn.fetchrow(query)
        if row:
            stats.distinct_count = row["distinct_count"]
            stats.null_count = row["null_count"]
            if row["total_count"] > 0:
                stats.null_ratio = row["null_count"] / row["total_count"]
        
        # Min/max for date and numeric types
        if self._is_minmax_type(column.data_type):
            query = f'SELECT MIN("{col_name}")::text, MAX("{col_name}")::text FROM {full_table}'
            row = await conn.fetchrow(query)
            if row:
                stats.min_value = row[0]
                stats.max_value = row[1]
    
    async def _collect_sqlserver_stats(
        self, full_table: str, col_name: str, column: Column, stats: ColumnStats
    ) -> None:
        """Collect statistics using SQL Server-specific queries."""
        cursor = self.introspector._cursor
        
        query = f"""
            SELECT 
                COUNT(DISTINCT [{col_name}]) as distinct_count,
                SUM(CASE WHEN [{col_name}] IS NULL THEN 1 ELSE 0 END) as null_count,
                COUNT(*) as total_count
            FROM {full_table}
        """
        cursor.execute(query)
        row = cursor.fetchone()
        if row:
            stats.distinct_count = row[0]
            stats.null_count = row[1]
            if row[2] > 0:
                stats.null_ratio = row[1] / row[2]
    
    async def _collect_db2_stats(
        self, full_table: str, col_name: str, column: Column, stats: ColumnStats
    ) -> None:
        """Collect statistics using DB2-specific queries."""
        import ibm_db
        conn = self.introspector._connection
        
        query = f"""
            SELECT COUNT(DISTINCT {col_name}), 
                   SUM(CASE WHEN {col_name} IS NULL THEN 1 ELSE 0 END),
                   COUNT(*)
            FROM {full_table}
        """
        stmt = ibm_db.exec_immediate(conn, query)
        row = ibm_db.fetch_tuple(stmt)
        if row:
            stats.distinct_count = row[0]
            stats.null_count = row[1]
            if row[2] > 0:
                stats.null_ratio = row[1] / row[2]
    
    def _is_minmax_type(self, data_type: str) -> bool:
        """Check if data type supports min/max operations."""
        minmax_types = {
            "integer", "int", "bigint", "smallint", "numeric", "decimal",
            "real", "double precision", "float", "money",
            "date", "timestamp", "timestamptz", "datetime", "datetime2",
            "timestamp without time zone", "timestamp with time zone",
        }
        return data_type.lower() in minmax_types

