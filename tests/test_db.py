import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    """Подменяет DB_PATH на временный файл."""
    db_file = str(tmp_path / "test.db")
    monkeypatch.setenv("DB_PATH", db_file)
    import importlib
    import db
    importlib.reload(db)
    db.init_db()
    return db


def _base_data(**kwargs):
    data = {
        "name": "Иван",
        "company": "ООО Завод",
        "email": "ivan@example.com",
        "phone": "+79991234567",
        "position": "Директор",
        "comment": "Вопрос",
        "marketing": True,
        "ip_address": "1.2.3.4",
    }
    data.update(kwargs)
    return data


def test_init_db_creates_table(tmp_db):
    import sqlite3, os
    conn = sqlite3.connect(os.environ["DB_PATH"])
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='responses'"
    )
    assert cur.fetchone() is not None
    conn.close()


def test_save_and_get_response(tmp_db):
    tmp_db.save_response(_base_data())
    rows = tmp_db.get_all_responses()
    assert len(rows) == 1
    assert rows[0]["name"] == "Иван"
    assert rows[0]["email"] == "ivan@example.com"
    assert rows[0]["ip_address"] == "1.2.3.4"
    assert rows[0]["consent_at"] != ""
    assert rows[0]["marketing"] == 1


def test_optional_fields_can_be_none(tmp_db):
    tmp_db.save_response(_base_data(position=None, comment=None, marketing=False, ip_address=None))
    rows = tmp_db.get_all_responses()
    assert rows[0]["position"] is None
    assert rows[0]["comment"] is None
    assert rows[0]["marketing"] == 0
    assert rows[0]["ip_address"] is None


def test_get_all_responses_newest_first(tmp_db):
    for i in range(3):
        tmp_db.save_response(_base_data(name=f"Юзер{i}", email=f"{i}@k.ru"))
    rows = tmp_db.get_all_responses()
    assert rows[0]["name"] == "Юзер2"
    assert rows[-1]["name"] == "Юзер0"


def test_migration_adds_missing_columns(tmp_path, monkeypatch):
    """Старая БД без новых колонок должна успешно мигрировать."""
    import sqlite3
    db_file = str(tmp_path / "old.db")
    monkeypatch.setenv("DB_PATH", db_file)
    # Создаём старую схему без новых полей
    conn = sqlite3.connect(db_file)
    conn.execute("""
        CREATE TABLE responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, company TEXT NOT NULL,
            email TEXT NOT NULL, phone TEXT NOT NULL,
            position TEXT, comment TEXT, created_at TEXT NOT NULL
        )
    """)
    conn.close()
    import importlib, db
    importlib.reload(db)
    db.init_db()  # должна добавить колонки без ошибок
    rows = db.get_all_responses()
    assert rows == []
