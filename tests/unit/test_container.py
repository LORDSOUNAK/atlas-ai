from __future__ import annotations

import os
from unittest import mock

from aetheros.config.settings import load_settings
from aetheros.container import Container


@mock.patch.dict(os.environ, {}, clear=True)
def test_container_initializes_with_defaults() -> None:
    container = Container()
    settings = container.config()

    assert settings.app_name == "aetheros"
    assert settings.app_env == "development"
    assert settings.debug is False


@mock.patch.dict(os.environ, {}, clear=True)
def test_container_exposes_settings_provider() -> None:
    container = Container()
    settings = container.settings()

    assert isinstance(settings, type(load_settings()))
    assert settings.app_name == "aetheros"
