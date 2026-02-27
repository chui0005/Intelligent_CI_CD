from __future__ import annotations

import logging
import shlex
import subprocess
from contextlib import asynccontextmanager

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
    return response


class RunRequest(BaseModel):
    cmd: str = Field(min_length=1, max_length=20, description="Allowlisted command key")


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


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
    if body.username != "demo-user" or body.password != "demo-password":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    logger.info("User login success for %s", body.username)
    return {"token": "demo-token-not-for-production"}


@app.get("/items")
def list_items(q: str = ""):
    return {"items": search_items(q)}
