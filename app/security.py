from __future__ import annotations

import hmac
import os

from fastapi import HTTPException

API_KEY_ENV = "APP_API_KEY"


def get_api_key() -> str:
    key = os.getenv(API_KEY_ENV)
    if not key:
        raise RuntimeError("APP_API_KEY not set")
    return key


def validate_api_key(api_key: str | None) -> None:
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    if not hmac.compare_digest(api_key, get_api_key()):
        raise HTTPException(status_code=401, detail="Invalid API key")
