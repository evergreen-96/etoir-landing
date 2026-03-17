import os
import pytest
from fastapi.testclient import TestClient

# Set test env vars BEFORE importing main
os.environ.setdefault("ADMIN_USER", "testadmin")
os.environ.setdefault("ADMIN_PASSWORD", "testpass")


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Each test gets a fresh DB."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    import importlib, db, main as m
    importlib.reload(db)
    importlib.reload(m)
    db.init_db()
    return m


@pytest.fixture
def client(isolated_db):
    return TestClient(isolated_db.app)


# ── POST /api/responses/ ──────────────────────────────────────────────────────

VALID_PAYLOAD = {
    "name": "Иван Петров",
    "company": "ООО Завод",
    "email": "ivan@zavod.ru",
    "phone": "+79991234567",
}


def test_post_response_returns_ok(client):
    r = client.post("/api/responses/", json=VALID_PAYLOAD)
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_post_response_saves_to_db(client, tmp_path, monkeypatch):
    client.post("/api/responses/", json=VALID_PAYLOAD)
    import db
    rows = db.get_all_responses()
    assert len(rows) == 1
    assert rows[0]["name"] == "Иван Петров"


def test_post_response_optional_fields_omitted(client):
    r = client.post("/api/responses/", json=VALID_PAYLOAD)
    assert r.status_code == 200


def test_post_response_optional_fields_provided(client):
    payload = {**VALID_PAYLOAD, "position": "Директор", "comment": "Вопрос"}
    r = client.post("/api/responses/", json=payload)
    assert r.status_code == 200


def test_post_response_missing_required_field_returns_422(client):
    bad = {k: v for k, v in VALID_PAYLOAD.items() if k != "email"}
    r = client.post("/api/responses/", json=bad)
    assert r.status_code == 422


# ── GET /admin/ ───────────────────────────────────────────────────────────────

def test_admin_requires_auth(client):
    r = client.get("/admin/")
    assert r.status_code == 401


def test_admin_wrong_password(client):
    r = client.get("/admin/", auth=("testadmin", "wrong"))
    assert r.status_code == 401


def test_admin_correct_auth_returns_html(client):
    r = client.get("/admin/", auth=("testadmin", "testpass"))
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_admin_shows_submitted_response(client):
    client.post("/api/responses/", json=VALID_PAYLOAD)
    r = client.get("/admin/", auth=("testadmin", "testpass"))
    assert "Иван Петров" in r.text
    assert "ООО Завод" in r.text


# ── GET /admin/export.csv ─────────────────────────────────────────────────────

def test_csv_export_requires_auth(client):
    r = client.get("/admin/export.csv")
    assert r.status_code == 401


def test_csv_export_contains_data(client):
    client.post("/api/responses/", json=VALID_PAYLOAD)
    r = client.get("/admin/export.csv", auth=("testadmin", "testpass"))
    assert r.status_code == 200
    assert "ivan@zavod.ru" in r.text
    assert "attachment" in r.headers.get("content-disposition", "")
