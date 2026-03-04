#!/usr/bin/env bash
set -euo pipefail

cat > app/security.py <<'PY'
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
PY

cat > app/utils.py <<'PY'
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent / "demo.db"


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
    conn.execute("INSERT INTO items(name) VALUES ('apple')")
    conn.execute("INSERT INTO items(name) VALUES ('banana')")
    conn.commit()
    conn.close()


def search_items(query: str) -> list[dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM items WHERE name LIKE ?", (f"%{query}%",))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row[0], "name": row[1]} for row in rows]
PY

cat > app/main.py <<'PY'
from __future__ import annotations

import hmac
import logging
import os
import shlex
import subprocess
from contextlib import asynccontextmanager
from secrets import token_urlsafe

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from app.security import validate_api_key
from app.utils import init_db, search_items

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

ALLOWED_COMMANDS = {
    "date": ["date"],
    "uptime": ["uptime"],
    "whoami": ["whoami"],
}


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Intelligent CI/CD Demo API", lifespan=lifespan)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Cache-Control"] = "no-store"
    if os.getenv("ENABLE_HSTS") == "1":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    return response


class RunRequest(BaseModel):
    cmd: str = Field(min_length=1, max_length=20, description="Allowlisted command key")


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


DEMO_USER = os.getenv("DEMO_USERNAME")
DEMO_PASS = os.getenv("DEMO_PASSWORD")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/run")
def run_command(body: RunRequest, x_api_key: str = Header(default="", alias="X-API-Key")):
    validate_api_key(x_api_key)
    command = body.cmd.strip()
    if command not in ALLOWED_COMMANDS:
        raise HTTPException(status_code=422, detail="Command not allowed")

    args = ALLOWED_COMMANDS[command]
    completed = subprocess.run(args, capture_output=True, text=True, timeout=3, check=False)
    return {"command": shlex.join(args), "output": completed.stdout.strip()}


@app.post("/login")
def login(body: LoginRequest):
    if not (DEMO_USER and DEMO_PASS):
        raise HTTPException(status_code=503, detail="Auth not configured")
    if not (
        hmac.compare_digest(body.username, DEMO_USER)
        and hmac.compare_digest(body.password, DEMO_PASS)
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    logger.info("User login success for %s", body.username)
    return {"token": token_urlsafe(32)}


@app.get("/items")
def list_items(q: str = ""):
    return {"items": search_items(q)}
PY

cat > requirements.txt <<'REQ'
fastapi==0.119.0
uvicorn==0.35.0
pytest==8.4.1
httpx==0.28.1
ruff==0.12.10
bandit==1.8.6
pip-audit==2.9.0
jinja2==3.1.6
REQ

cat > tests/test_main.py <<'PY'
import os

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_run_rejects_disallowed_command() -> None:
    os.environ["APP_API_KEY"] = "test-key"
    response = client.post(
        "/run",
        headers={"X-API-Key": "test-key"},
        json={"cmd": "cat /etc/passwd"},
    )
    assert response.status_code == 422
PY

echo "Re-applied fixed secure code."
