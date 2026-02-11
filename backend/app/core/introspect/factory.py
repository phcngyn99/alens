"""
Factory for creating database introspectors.
Implements the Strategy pattern - returns the appropriate introspector based on database type.
"""
from typing import Type

from app.core.introspect.base import BaseIntrospector, ConnectionConfig, DriverStatus
from app.core.introspect.db2 import DB2Introspector
from app.core.introspect.postgresql import PostgreSQLIntrospector
from app.core.introspect.sqlserver import SQLServerIntrospector

# Registry of supported database types and their introspectors
INTROSPECTOR_REGISTRY: dict[str, Type[BaseIntrospector]] = {
    "postgresql": PostgreSQLIntrospector,
    "postgres": PostgreSQLIntrospector,  # Alias
    "sqlserver": SQLServerIntrospector,
    "mssql": SQLServerIntrospector,  # Alias
    "db2": DB2Introspector,
    "ibm_db2": DB2Introspector,  # Alias
}


def get_introspector(db_type: str, config: ConnectionConfig) -> BaseIntrospector:
    """
    Factory function to get the appropriate introspector for a database type.
    
    Args:
        db_type: Database type identifier (e.g., 'postgresql', 'sqlserver', 'db2')
        config: Connection configuration
        
    Returns:
        Appropriate introspector instance
        
    Raises:
        ValueError: If database type is not supported
    """
    db_type_lower = db_type.lower()
    
    if db_type_lower not in INTROSPECTOR_REGISTRY:
        supported = list(set(INTROSPECTOR_REGISTRY.keys()))
        raise ValueError(
            f"Unsupported database type: {db_type}. "
            f"Supported types: {', '.join(sorted(supported))}"
        )
    
    introspector_class = INTROSPECTOR_REGISTRY[db_type_lower]
    return introspector_class(config)


def get_supported_databases() -> list[str]:
    """Return list of supported database types (primary names only)."""
    return ["postgresql", "sqlserver", "db2"]


def check_all_drivers() -> dict[str, DriverStatus]:
    """Check the status of all database drivers."""
    return {
        "postgresql": PostgreSQLIntrospector.check_driver(),
        "sqlserver": SQLServerIntrospector.check_driver(),
        "db2": DB2Introspector.check_driver(),
    }


def check_driver(db_type: str) -> DriverStatus:
    """Check the status of a specific database driver."""
    db_type_lower = db_type.lower()
    
    if db_type_lower not in INTROSPECTOR_REGISTRY:
        raise ValueError(f"Unsupported database type: {db_type}")
    
    introspector_class = INTROSPECTOR_REGISTRY[db_type_lower]
    return introspector_class.check_driver()

