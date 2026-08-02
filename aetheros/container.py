from __future__ import annotations

from dependency_injector import containers, providers

from aetheros.config.settings import Settings, load_settings


class Container(containers.DeclarativeContainer):
    """Dependency injection container for the AetherOS foundation package."""

    config = providers.Resource(load_settings)
    settings = providers.Singleton(Settings)

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.config()  # Trigger initialization so misconfiguration fails early.
