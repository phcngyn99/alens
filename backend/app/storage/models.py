"""
SQLAlchemy models for application persistence.
Stores database connections, user intents, and AI outputs.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.storage.database import Base


class UserRole(str, PyEnum):
    """User roles for RBAC."""

    ADMIN = "admin"
    USER = "user"


class User(Base):
    """User account for authentication."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(
        String(20), default=UserRole.USER.value
    )  # admin or user
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    connections: Mapped[list["DatabaseConnection"]] = relationship(
        back_populates="owner"
    )
    ai_credentials: Mapped[list["AICredential"]] = relationship(back_populates="user")


class DatabaseConnection(Base):
    """Stored database connection configuration."""

    __tablename__ = "database_connections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )

    name: Mapped[str] = mapped_column(String(100))
    db_type: Mapped[str] = mapped_column(String(50))  # postgresql, sqlserver, db2
    host: Mapped[str] = mapped_column(String(255))
    port: Mapped[int] = mapped_column(Integer)
    database_name: Mapped[str] = mapped_column(String(100))
    username: Mapped[str] = mapped_column(String(100))
    encrypted_password: Mapped[str] = mapped_column(Text)  # Encrypted with Fernet
    schema_whitelist: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # List of allowed schemas

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="connections")
    intents: Mapped[list["AnalyticalIntent"]] = relationship(
        back_populates="connection"
    )


class AnalyticalIntent(Base):
    """Structured user analytical intent - versioned."""

    __tablename__ = "analytical_intents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("database_connections.id")
    )
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Structured intent fields
    business_domain: Mapped[str] = mapped_column(Text)
    analytical_goal: Mapped[str] = mapped_column(String(50))  # reporting, bi, ad-hoc
    time_grain: Mapped[str] = mapped_column(String(50))  # daily, weekly, monthly
    key_metrics: Mapped[list] = mapped_column(JSON)  # List of metric names
    tables_of_interest: Mapped[list] = mapped_column(
        JSON
    )  # List of table names with hints
    exclusions: Mapped[list] = mapped_column(JSON)  # Tables/schemas to exclude

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    connection: Mapped["DatabaseConnection"] = relationship(back_populates="intents")
    ai_outputs: Mapped[list["AIOutput"]] = relationship(back_populates="intent")


class AIOutput(Base):
    """Versioned AI-generated dimensional model outputs."""

    __tablename__ = "ai_outputs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    intent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analytical_intents.id")
    )
    version: Mapped[int] = mapped_column(Integer, default=1)

    # AI outputs
    model_explanation: Mapped[str] = mapped_column(Text)  # Fact tables, grain, measures
    dimension_details: Mapped[dict] = mapped_column(JSON)  # Attributes, SCD hints
    assumptions: Mapped[str] = mapped_column(Text)  # Assumptions and uncertainties
    dimensional_dbml: Mapped[str] = mapped_column(Text)  # Generated DBML

    # Metadata
    ai_provider: Mapped[str] = mapped_column(String(50))
    ai_model: Mapped[str] = mapped_column(String(100))
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    intent: Mapped["AnalyticalIntent"] = relationship(back_populates="ai_outputs")


class AICredential(Base):
    """
    Stored AI API credentials (encrypted).

    Supports providers:
    - openai: Standard OpenAI API
    - anthropic: Standard Anthropic API
    - azure_openai: Azure OpenAI Service
    - azure_anthropic: Azure AI Services (Anthropic models)
    """

    __tablename__ = "ai_credentials"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )

    # Provider: openai, anthropic, azure_openai, azure_anthropic
    provider: Mapped[str] = mapped_column(String(50))
    encrypted_api_key: Mapped[str] = mapped_column(Text)
    model_name: Mapped[str] = mapped_column(String(100))
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096)

    # Azure-specific fields (nullable for non-Azure providers)
    endpoint_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    deployment_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    api_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="ai_credentials")
