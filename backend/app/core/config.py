"""Application Configuration Module.

Manages all application and database settings using Pydantic Settings
and python-dotenv. Settings are loaded from environment variables and
an optional local '.env' file.
"""

from functools import lru_cache
from typing import List, Union, Optional
import json
import urllib.parse
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings schema and validator.

    Reads variables from environment or a local .env file.
    Default values provide safe, working development defaults.
    """

    # 1. Application Metadata
    APP_NAME: str = "MEVShield API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Educational MEV analysis and simulation platform for Ethereum"

    # 2. Runtime Environment
    # Standard environments: 'development', 'staging', 'production'
    ENVIRONMENT: str = "development"

    # 3. API Prefix Configuration
    # All routes will be grouped under this prefix (e.g., /api/health)
    API_PREFIX: str = "/api"

    # 4. Interactive Documentation
    # Swagger UI (/docs) and ReDoc (/redoc) availability flag
    DOCS_ENABLED: Optional[bool] = None

    # 5. Cross-Origin Resource Sharing (CORS)
    # List of allowed origins for web clients (e.g., React frontend)
    ALLOWED_ORIGINS: Union[str, List[str]] = ["http://localhost:5173"]

    # 6. Database Configuration (Phase 2)
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "mevshield"
    DATABASE_USER: str = "mevshield_user"
    DATABASE_PASSWORD: str = "replace_with_local_password"
    # Optional direct database connection string (overrides individual components if provided)
    DATABASE_URL: Optional[str] = None

    # Database Connection Pool Settings (tuned for small academic application)
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    # Configuration for pydantic-settings
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        """Ensure environment is lowercase and a recognized deployment stage."""
        normalized = value.strip().lower()
        allowed = {"development", "staging", "production"}
        if normalized not in allowed:
            return "development"
        return normalized

    @field_validator("API_PREFIX")
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        """Ensure API prefix starts with a forward slash and has no trailing slash."""
        prefix = value.strip()
        if not prefix.startswith("/"):
            prefix = "/" + prefix
        if prefix.endswith("/") and len(prefix) > 1:
            prefix = prefix.rstrip("/")
        return prefix

    @field_validator("ALLOWED_ORIGINS", mode="after")
    @classmethod
    def parse_allowed_origins(cls, value: Union[str, List[str]]) -> List[str]:
        """Parse allowed origins from a comma-separated string, JSON list, or Python list."""
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        return [str(origin).strip() for origin in parsed if str(origin).strip()]
                except json.JSONDecodeError:
                    pass
            return [origin.strip() for origin in value.split(",") if origin.strip()]

        if isinstance(value, list):
            return [str(origin).strip() for origin in value if str(origin).strip()]

        return ["http://localhost:5173"]

    @property
    def is_production(self) -> bool:
        """Helper property to check if current environment is production."""
        return self.ENVIRONMENT == "production"

    @property
    def is_docs_enabled(self) -> bool:
        """Determines if interactive docs should be accessible."""
        if self.DOCS_ENABLED is not None:
            return self.DOCS_ENABLED
        return not self.is_production

    @property
    def sqlalchemy_database_url(self) -> str:
        """Construct a safe SQLAlchemy connection URL for PostgreSQL.

        Uses the modern `postgresql+psycopg` dialect driver.
        Safely URL-encodes special characters in user passwords.
        """
        if self.DATABASE_URL:
            # If a complete URL is provided, ensure dialect is psycopg3 compatible if postgresql://
            url = self.DATABASE_URL
            if url.startswith("postgresql://") and not url.startswith("postgresql+"):
                url = url.replace("postgresql://", "postgresql+psycopg://", 1)
            return url

        # Safely encode credentials to handle special characters (e.g. '@', ':', '/')
        encoded_user = urllib.parse.quote_plus(self.DATABASE_USER)
        encoded_password = urllib.parse.quote_plus(self.DATABASE_PASSWORD)

        return (
            f"postgresql+psycopg://{encoded_user}:{encoded_password}@"
            f"{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )


@lru_cache
def get_settings() -> Settings:
    """Creates and caches a singleton instance of the application settings."""
    return Settings()


# Convenient global settings instance
settings = get_settings()
