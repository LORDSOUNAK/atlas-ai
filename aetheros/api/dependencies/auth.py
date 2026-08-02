from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from aetheros.config.settings import load_settings

security = HTTPBearer(auto_error=False)


def require_api_auth(
    authorization: HTTPAuthorizationCredentials | None = Security(security),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    settings = load_settings()
    # Allow either a matching static API key (X-API-Key) or a Bearer token equal to jwt_secret_key
    if x_api_key and settings.api_key and x_api_key == settings.api_key:
        return None

    if authorization and authorization.scheme.lower() == "bearer":
        token = authorization.credentials
        if token == settings.jwt_secret_key:
            return None

    raise HTTPException(status_code=401, detail="UNAUTHORIZED")
