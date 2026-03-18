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


def test_init_db_creates_table(tmp_db):
    import sqlite3, os
    conn = sqlite3.connect(os.environ["DB_PATH"])
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='responses'"
    )
    assert cur.fetchone() is not None
    conn.close()


def test_save_and_get_response(tmp_db):
    data = {
        "name": "Иван",
        "company": "ООО Завод",
        "email": "ivan@example.com",
        "phone": "+79991234567",
        "position": "Директор",
        "comment": "Вопрос",
        "marketing": True,
    }
    tmp_db.save_response(data)
    rows = tmp_db.get_all_responses()
    assert len(rows) == 1
    assert rows[0]["name"] == "Иван"
    assert rows[0]["company"] == "ООО Завод"
    assert rows[0]["email"] == "ivan@example.com"
    assert rows[0]["marketing"] == 1


def test_optional_fields_can_be_none(tmp_db):
    data = {
        "name": "Пётр",
        "company": "ИП",
        "email": "p@p.ru",
        "phone": "+79990000000",
        "position": None,
        "comment": None,
        "marketing": False,
    }
    tmp_db.save_response(data)
    rows = tmp_db.get_all_responses()
    assert rows[0]["position"] is None
    assert rows[0]["comment"] is None
    assert rows[0]["marketing"] == 0


def test_get_all_responses_newest_first(tmp_db):
    for i in range(3):
        tmp_db.save_response({
            "name": f"Юзер{i}", "company": "К", "email": f"{i}@k.ru",
            "phone": "+7", "position": None, "comment": None, "marketing": True,
        })
    rows = tmp_db.get_all_responses()
    assert rows[0]["name"] == "Юзер2"
    assert rows[-1]["name"] == "Юзер0"
