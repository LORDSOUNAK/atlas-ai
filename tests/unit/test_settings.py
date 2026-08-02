from __future__ import annotations

import os
from unittest import mock

from aetheros.config.settings import Settings, load_settings


@mock.patch.dict(os.environ, {}, clear=True)
def test_load_settings_uses_defaults() -> None:
    settings = load_settings()

    assert settings.app_name == "aetheros"
    assert settings.app_env == "development"
    assert settings.debug is False
    assert settings.api_prefix == "/api/v1"


@mock.patch.dict(
    os.environ,
    {
        "APP_NAME": "custom-app",
        "APP_ENV": "production",
        "DEBUG": "true",
        "POSTGRES_URL": "postgresql://example:example@localhost:5432/example",
        "REDIS_URL": "redis://example:6379/0",
    },
    clear=True,
)
def test_settings_reads_env_values() -> None:
    settings = Settings()

    assert settings.app_name == "custom-app"
    assert settings.app_env == "production"
    assert settings.debug is True
    assert (
        settings.postgres_url == "postgresql://example:example@localhost:5432/example"
    )
    assert settings.redis_url == "redis://example:6379/0"


def test_load_settings_returns_settings_instance() -> None:
    settings = load_settings()

    assert isinstance(settings, Settings)
