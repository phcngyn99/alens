"""
Domain models for database schema representation.
These are pure data classes representing introspected schema metadata.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Column:
    """Represents a database column."""
    name: str
    data_type: str
    nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    default_value: Optional[str] = None
    comment: Optional[str] = None
    
    # Optional statistics (observed, not guaranteed)
    row_count: Optional[int] = None
    distinct_count: Optional[int] = None
    null_ratio: Optional[float] = None
    min_value: Optional[str] = None
    max_value: Optional[str] = None


@dataclass
class PrimaryKey:
    """Represents a primary key constraint."""
    name: str
    columns: list[str] = field(default_factory=list)


@dataclass
class ForeignKey:
    """Represents a foreign key constraint."""
    name: str
    columns: list[str] = field(default_factory=list)
    referenced_schema: str = ""
    referenced_table: str = ""
    referenced_columns: list[str] = field(default_factory=list)


@dataclass
class Index:
    """Represents a database index."""
    name: str
    columns: list[str] = field(default_factory=list)
    is_unique: bool = False
    is_primary: bool = False


@dataclass
class Table:
    """Represents a database table with its columns and constraints."""
    schema_name: str
    name: str
    columns: list[Column] = field(default_factory=list)
    primary_key: Optional[PrimaryKey] = None
    foreign_keys: list[ForeignKey] = field(default_factory=list)
    indexes: list[Index] = field(default_factory=list)
    comment: Optional[str] = None
    
    # Optional statistics
    approximate_row_count: Optional[int] = None
    
    # Hints for dimensional modeling
    has_timestamp_columns: bool = False
    fk_count: int = 0
    
    @property
    def full_name(self) -> str:
        """Return fully qualified table name."""
        return f"{self.schema_name}.{self.name}"
    
    def get_primary_key_columns(self) -> list[str]:
        """Return list of primary key column names."""
        if self.primary_key:
            return self.primary_key.columns
        return [c.name for c in self.columns if c.is_primary_key]


@dataclass
class Schema:
    """Represents a database schema containing tables."""
    name: str
    tables: list[Table] = field(default_factory=list)
    
    def get_table(self, table_name: str) -> Optional[Table]:
        """Find a table by name."""
        for table in self.tables:
            if table.name == table_name:
                return table
        return None

