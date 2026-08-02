# AetherOS Foundation

This workspace contains the initial foundation for the AetherOS platform.

## Included in this implementation

- A Python package scaffold for the backend application
- Configuration loading with pydantic-settings
- A dependency injection container for wiring services and infrastructure components
- A simple FastAPI application entrypoint
- Agent runtime lifecycle support with create, start, stop, pause, resume, and human-feedback handling
- Unit tests for configuration loading, container initialization, and agent lifecycle behavior

## Development commands

Install dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Run linting:

```bash
ruff check .
black --check .
mypy aetheros
```
