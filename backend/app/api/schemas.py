"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============ Auth Schemas ============


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


# ============ User Schemas ============


class UserResponse(BaseModel):
    id: UUID
    username: str
    role: Literal["admin", "user"]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)
    role: Literal["admin", "user"] = "user"
    is_active: bool = True


class UserUpdate(BaseModel):
    role: Optional[Literal["admin", "user"]] = None
    is_active: Optional[bool] = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6)


# ============ Database Connection Schemas ============


class ConnectionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    db_type: Literal["postgresql", "sqlserver", "db2"]
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(..., ge=1, le=65535)
    database_name: str = Field(..., min_length=1, max_length=100)
    username: str = Field(..., min_length=1, max_length=100)
    schema_whitelist: Optional[list[str]] = None


class ConnectionCreate(ConnectionBase):
    password: str = Field(..., min_length=1)


class ConnectionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    host: Optional[str] = Field(None, min_length=1, max_length=255)
    port: Optional[int] = Field(None, ge=1, le=65535)
    database_name: Optional[str] = Field(None, min_length=1, max_length=100)
    username: Optional[str] = Field(None, min_length=1, max_length=100)
    password: Optional[str] = Field(None, min_length=1)
    schema_whitelist: Optional[list[str]] = None


class ConnectionResponse(ConnectionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConnectionTestResult(BaseModel):
    success: bool
    message: str


class DriverStatusResponse(BaseModel):
    driver_name: str
    is_installed: bool
    version: Optional[str] = None
    install_instructions: Optional[str] = None


# ============ Schema Introspection Schemas ============


class ColumnResponse(BaseModel):
    name: str
    data_type: str
    nullable: bool
    is_primary_key: bool
    is_foreign_key: bool
    default_value: Optional[str] = None
    comment: Optional[str] = None


class ForeignKeyResponse(BaseModel):
    name: str
    columns: list[str]
    referenced_schema: str
    referenced_table: str
    referenced_columns: list[str]


class TableResponse(BaseModel):
    schema_name: str
    name: str
    columns: list[ColumnResponse]
    foreign_keys: list[ForeignKeyResponse]
    approximate_row_count: Optional[int] = None
    has_timestamp_columns: bool
    fk_count: int
    hint: Optional[str] = None  # "event-like" or "reference-like"


class SchemaResponse(BaseModel):
    name: str
    tables: list[TableResponse]


class TableDataPreviewResponse(BaseModel):
    """Response for table data preview."""

    schema_name: str
    table_name: str
    columns: list[str]
    rows: list[list]
    row_count: int


# ============ Analytical Intent Schemas ============


class TableOfInterest(BaseModel):
    name: str
    is_likely_fact: bool = False
    is_likely_dimension: bool = False
    description: Optional[str] = None


class IntentCreate(BaseModel):
    connection_id: UUID
    business_domain: str = Field(..., min_length=1)
    analytical_goal: Literal["reporting", "bi", "ad-hoc"]
    time_grain: Literal["daily", "weekly", "monthly"]
    key_metrics: list[str]
    tables_of_interest: list[TableOfInterest]
    exclusions: list[str] = []


class IntentResponse(BaseModel):
    id: UUID
    connection_id: UUID
    version: int
    business_domain: str
    analytical_goal: str
    time_grain: str
    key_metrics: list[str]
    tables_of_interest: list[dict]
    exclusions: list[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============ AI Output Schemas ============


class GenerateModelRequest(BaseModel):
    intent_id: UUID
    include_statistics: bool = False


class AIOutputResponse(BaseModel):
    id: UUID
    intent_id: UUID
    version: int
    model_explanation: str
    dimension_details: dict
    assumptions: str
    dimensional_dbml: str
    ai_provider: str
    ai_model: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============ AI Credentials Schemas ============

# Supported AI providers
AIProviderType = Literal["openai", "anthropic", "azure_openai", "azure_anthropic"]


class AICredentialCreate(BaseModel):
    """
    Create AI credential.

    For standard providers (openai, anthropic):
    - api_key: API key from the provider
    - model_name: Model name (e.g., gpt-4-turbo, claude-3-opus-20240229)

    For Azure providers (azure_openai, azure_anthropic):
    - api_key: Azure API key
    - model_name: Model/deployment name
    - endpoint_url: Azure endpoint URL (e.g., https://your-resource.openai.azure.com)
    - deployment_name: Azure deployment name (optional, defaults to model_name)
    - api_version: API version (e.g., 2024-02-15-preview for OpenAI, 2023-06-01 for Anthropic)
    """

    provider: AIProviderType
    api_key: str = Field(..., min_length=1)
    model_name: str = Field(..., min_length=1)
    max_tokens: int = Field(default=4096, ge=100, le=100000)

    # Azure-specific fields (required for azure_* providers)
    endpoint_url: Optional[str] = Field(None, min_length=1)
    deployment_name: Optional[str] = Field(None, min_length=1)
    api_version: Optional[str] = Field(None, min_length=1)


class AICredentialResponse(BaseModel):
    id: UUID
    provider: str
    model_name: str
    max_tokens: int
    endpoint_url: Optional[str] = None
    deployment_name: Optional[str] = None
    api_version: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
