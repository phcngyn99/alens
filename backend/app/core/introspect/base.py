"""
Base introspector interface using the Strategy pattern.
All database-specific introspectors must implement this interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from app.core.models.schema import Schema, Table


@dataclass
class ConnectionConfig:
    """Configuration for connecting to a database."""

    host: str
    port: int
    database: str
    username: str
    password: str
    schema_whitelist: Optional[list[str]] = None


@dataclass
class DriverStatus:
    """Status of a database driver."""

    driver_name: str
    is_installed: bool
    version: Optional[str] = None
    install_instructions: Optional[str] = None


class BaseIntrospector(ABC):
    """
    Abstract base class for database introspection.

    Implements the Strategy pattern - each database type has its own
    concrete implementation that queries system catalogs appropriately.

    All operations are READ-ONLY. No data modification is allowed.
    """

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self._connection = None

    @property
    @abstractmethod
    def db_type(self) -> str:
        """Return the database type identifier (e.g., 'postgresql', 'sqlserver', 'db2')."""
        pass

    @classmethod
    @abstractmethod
    def check_driver(cls) -> DriverStatus:
        """Check if the required database driver is installed."""
        pass

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish a connection to the database.
        Returns True if successful, False otherwise.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the database connection."""
        pass

    @abstractmethod
    async def test_connection(self) -> tuple[bool, str]:
        """
        Test the database connection.
        Returns (success, message) tuple.
        """
        pass

    @abstractmethod
    async def get_schemas(self) -> list[str]:
        """
        Get list of schema names.
        Respects schema_whitelist if configured.
        """
        pass

    @abstractmethod
    async def get_tables(self, schema_name: str) -> list[str]:
        """Get list of table names in a schema."""
        pass

    @abstractmethod
    async def introspect_table(self, schema_name: str, table_name: str) -> Table:
        """
        Fully introspect a single table.
        Returns Table with columns, primary keys, foreign keys, and indexes.
        """
        pass

    async def introspect_schema(self, schema_name: str) -> Schema:
        """
        Introspect all tables in a schema.
        Default implementation calls introspect_table for each table.
        """
        table_names = await self.get_tables(schema_name)
        tables = []
        for table_name in table_names:
            table = await self.introspect_table(schema_name, table_name)
            tables.append(table)
        return Schema(name=schema_name, tables=tables)

    @abstractmethod
    async def get_sample_data(
        self, schema_name: str, table_name: str, limit: int = 20
    ) -> tuple[list[str], list[list]]:
        """
        Get sample data from a table for preview.

        Args:
            schema_name: Schema name
            table_name: Table name
            limit: Maximum number of rows to return (default 20)

        Returns:
            Tuple of (column_names, rows) where rows is a list of lists
        """
        pass

    def get_last_error(self) -> str:
        """Get the last connection error message. Override in subclasses."""
        return getattr(self, "_last_error", "Unknown error")

    async def __aenter__(self):
        """Async context manager entry."""
        connected = await self.connect()
        if not connected:
            error_msg = self.get_last_error()
            raise ConnectionError(f"Failed to connect to database: {error_msg}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
