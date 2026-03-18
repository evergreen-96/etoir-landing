"""
db.py — SQLite-слой для хранения заявок с лендинга.
"""
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.environ.get("DB_PATH", "/data/responses.db")


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT NOT NULL,
                company      TEXT NOT NULL,
                email        TEXT NOT NULL,
                phone        TEXT NOT NULL,
                position     TEXT,
                comment      TEXT,
                marketing    INTEGER NOT NULL DEFAULT 1,
                ip_address   TEXT,
                consent_at   TEXT NOT NULL,
                created_at   TEXT NOT NULL
            )
        """)
        # Миграция: добавить колонки если их нет (для существующих БД)
        existing = {
            row[1]
            for row in conn.execute("PRAGMA table_info(responses)").fetchall()
        }
        for col, definition in [
            ("marketing",  "INTEGER NOT NULL DEFAULT 1"),
            ("ip_address", "TEXT"),
            ("consent_at", "TEXT NOT NULL DEFAULT ''"),
        ]:
            if col not in existing:
                conn.execute(f"ALTER TABLE responses ADD COLUMN {col} {definition}")


def save_response(data: dict):
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO responses
                (name, company, email, phone, position, comment,
                 marketing, ip_address, consent_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["name"],
                data["company"],
                data["email"],
                data["phone"],
                data.get("position"),
                data.get("comment"),
                1 if data.get("marketing", True) else 0,
                data.get("ip_address"),
                now,
                now,
            ),
        )


def get_all_responses() -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM responses ORDER BY id DESC"
        ).fetchall()
    return [dict(r) for r in rows]
