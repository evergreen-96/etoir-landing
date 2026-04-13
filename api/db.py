import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

DB_PATH = "/data/responses.db"


def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                name              TEXT NOT NULL,
                company           TEXT NOT NULL,
                email             TEXT NOT NULL,
                phone             TEXT NOT NULL,
                position          TEXT,
                comment           TEXT,
                created_at        TEXT NOT NULL,
                consent_privacy   INTEGER NOT NULL DEFAULT 1,
                consent_marketing INTEGER NOT NULL DEFAULT 0
            )
        """)
        # migrate existing DB
        for col, default in [("consent_privacy", 1), ("consent_marketing", 0)]:
            try:
                conn.execute(f"ALTER TABLE responses ADD COLUMN {col} INTEGER NOT NULL DEFAULT {default}")
            except Exception:
                pass


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def save_response(name, company, email, phone, position, comment,
                  consent_privacy: bool = True, consent_marketing: bool = False):
    created_at = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO responses "
            "(name, company, email, phone, position, comment, created_at, "
            "consent_privacy, consent_marketing) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (name, company, email, phone, position, comment, created_at,
             int(consent_privacy), int(consent_marketing)),
        )


def get_all_responses():
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM responses ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]
