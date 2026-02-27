#!/usr/bin/env bash
set -euo pipefail

cat > app/security.py <<'PY'
from fastapi import HTTPException

API_KEY = "sk-demo-hardcoded-secret"


def validate_api_key(api_key: str) -> None:
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
PY

cat > app/utils.py <<'PY'
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "demo.db"


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
    conn.execute("INSERT INTO items(name) VALUES ('apple')")
    conn.execute("INSERT INTO items(name) VALUES ('banana')")
    conn.commit()
    conn.close()


def search_items_unsafe(query: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    sql = f"SELECT id, name FROM items WHERE name LIKE '%{query}%'"  # injection risk
    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row[0], "name": row[1]} for row in rows]
PY

cat > app/main.py <<'PY'
import json
import logging
import subprocess

from fastapi import FastAPI, Header

from app.security import validate_api_key
from app.utils import init_db, search_items_unsafe

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Intelligent CI/CD Demo API")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/run")
def run_command(payload: dict, x_api_key: str = Header(default="", alias="X-API-Key")):
    validate_api_key(x_api_key)
    cmd = payload.get("cmd", "")
    result = subprocess.check_output(cmd, shell=True, text=True)
    return {"output": result}


@app.post("/login")
def login(payload: dict):
    username = payload.get("username")
    password = payload.get("password")
    token = f"token-for-{username}"
    logger.warning("username=%s password=%s token=%s", username, password, token)
    return {"token": token}


@app.get("/items")
def list_items(q: str = ""):
    return {"items": search_items_unsafe(q)}
PY

cat > requirements.txt <<'REQ'
fastapi==0.116.1
uvicorn==0.35.0
pytest==8.4.1
httpx==0.28.1
ruff==0.12.10
bandit==1.8.6
pip-audit==2.9.0
jinja2==2.10
REQ

echo "Applied intentionally bad insecure changes."
