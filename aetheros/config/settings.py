from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for the AetherOS foundation package."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="aetheros", description="Application name")
    app_env: str = Field(default="development", description="Runtime environment")
    debug: bool = Field(default=False, description="Enable debug mode")
    postgres_url: str = Field(
        default="postgresql://aetheros:aetheros@localhost:5432/aetheros",
        description="PostgreSQL connection URL",
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    jwt_secret_key: str = Field(
        default="change-me-in-production",
        description="JWT signing secret",
    )
    api_key: str = Field(
        default="",
        description="Static API key for simple dev/testing auth",
    )
    langfuse_public_key: str = Field(default="", description="Langfuse public key")
    langfuse_secret_key: str = Field(default="", description="Langfuse secret key")
    openai_api_key: str = Field(default="", description="OpenAI API key")
    api_prefix: str = Field(default="/api/v1", description="API route prefix")


def load_settings() -> Settings:
    """Load application settings from environment variables."""
    return Settings()
