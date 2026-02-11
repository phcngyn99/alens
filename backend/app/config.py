"""
Application configuration using pydantic-settings.
All configuration is loaded from environment variables with sensible defaults.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Alens"
    app_version: str = "0.1.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database (application storage - PostgreSQL)
    database_url: str = "postgresql+asyncpg://alens:alens@localhost:5432/alens"

    # Security
    secret_key: str = "change-this-in-production-use-openssl-rand-hex-32"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Encryption key for storing database passwords
    encryption_key: str = "change-this-32-byte-key-in-prod!"

    # Default admin user
    default_username: str = "wnkadmin"
    default_password: str = "wnkadmin"

    # AI Configuration
    ai_provider: Literal["openai", "anthropic"] = "openai"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ai_model: str = "gpt-4-turbo-preview"
    ai_max_tokens: int = 4096
    ai_temperature: float = 0.1  # Low temperature for deterministic outputs

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Cache settings
    cache_ttl_seconds: int = 300  # 5 minutes default TTL for schema introspection
    cache_preview_ttl_seconds: int = (
        60  # 1 minute for table previews (data changes more often)
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
