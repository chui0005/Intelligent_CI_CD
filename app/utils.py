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
