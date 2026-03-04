from __future__ import annotations

import hmac
import logging
import os
import shlex
import subprocess
from contextlib import asynccontextmanager
from secrets import token_urlsafe

from fastapi import FastAPI, Header, HTTPException, Query
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
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
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
def list_items(q: str = Query(default="", max_length=64)):
    return {"items": search_items(q)}
