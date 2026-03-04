from __future__ import annotations

import hmac
import os

from fastapi import HTTPException

API_KEY_ENV = "APP_API_KEY"
DEFAULT_DEMO_KEY = "change-me-in-production"


def get_api_key() -> str:
    return os.getenv(API_KEY_ENV, DEFAULT_DEMO_KEY)


def validate_api_key(api_key: str | None) -> None:
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    if not hmac.compare_digest(api_key, get_api_key()):
        raise HTTPException(status_code=401, detail="Invalid API key")
