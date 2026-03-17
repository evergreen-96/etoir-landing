"""
db.py — SQLite-слой для хранения заявок с лендинга.
"""
import contextlib
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.environ.get("DB_PATH", "/data/responses.db")


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with contextlib.closing(_conn()) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                company    TEXT NOT NULL,
                email      TEXT NOT NULL,
                phone      TEXT NOT NULL,
                position   TEXT,
                comment    TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


def save_response(data: dict):
    with contextlib.closing(_conn()) as conn:
        conn.execute(
            """
            INSERT INTO responses
                (name, company, email, phone, position, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["name"],
                data["company"],
                data["email"],
                data["phone"],
                data.get("position"),
                data.get("comment"),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()


def get_all_responses() -> list[dict]:
    with contextlib.closing(_conn()) as conn:
        rows = conn.execute(
            "SELECT * FROM responses ORDER BY id DESC"
        ).fetchall()
    return [dict(r) for r in rows]
