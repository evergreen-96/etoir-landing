# Telegram Notifications Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Send a Telegram notification to a configured chat when a new lead form is submitted via `POST /api/responses/`.

**Architecture:** A new `notify.py` module handles all TG logic (build message text + HTTP call). `main.py` calls `notify.send_telegram(notify.build_message(payload))` after saving to DB. Fire-and-forget: all errors are logged and swallowed. No new pip dependencies — uses stdlib `urllib.request`.

**Tech Stack:** Python stdlib (`urllib.request`, `json`, `logging`), pytest + monkeypatch for tests.

---

## File Map

| Action | File | Responsibility |
|---|---|---|
| Create | `notify.py` | Build TG message text; send HTTP POST to TG Bot API |
| Create | `tests/test_notify.py` | Unit tests for `build_message` and `send_telegram` |
| Modify | `main.py` | Call `notify.send_telegram(notify.build_message(payload))` after DB save |
| Modify | `tests/test_api.py` | Add `autouse` fixture to monkeypatch `notify.send_telegram` to a no-op |
| Modify | `.env.example` | Document `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` variables |

---

## Task 1: Create `notify.py` with TDD

**Files:**
- Create: `notify.py`
- Create: `tests/test_notify.py`

### Subtask 1a — `build_message`

- [ ] **Step 1: Write failing tests for `build_message`**

Create `tests/test_notify.py`:

```python
import notify

SAMPLE = {
    "name": "Иван Петров",
    "company": "ООО Завод",
    "phone": "+79991234567",
    "email": "ivan@zavod.ru",
    "position": None,
    "comment": None,
}


def test_build_message_contains_required_fields():
    msg = notify.build_message(SAMPLE)
    assert "📬 Новая заявка с etoir.ru" in msg
    assert "Иван Петров" in msg
    assert "ООО Завод" in msg
    assert "+79991234567" in msg
    assert "ivan@zavod.ru" in msg


def test_build_message_no_none_literals():
    msg = notify.build_message(SAMPLE)
    assert "None" not in msg


def test_build_message_optional_fields_shown_when_present():
    data = {**SAMPLE, "position": "Директор", "comment": "Интересует демо"}
    msg = notify.build_message(data)
    assert "Директор" in msg
    assert "Интересует демо" in msg


def test_build_message_optional_fields_absent_when_none():
    msg = notify.build_message(SAMPLE)
    assert "Должность" not in msg
    assert "Комментарий" not in msg
```

- [ ] **Step 2: Run tests — verify they FAIL**

```bash
cd D:/prod_projects/toir-landing && pytest tests/test_notify.py -v
```

Expected: `ModuleNotFoundError: No module named 'notify'`

- [ ] **Step 3: Implement `build_message` in `notify.py`**

Create `notify.py`:

```python
"""
notify.py — Telegram notifications for etoir.ru lead form submissions.
"""
import json
import logging
import os
import urllib.request

logger = logging.getLogger(__name__)


def build_message(data: dict) -> str:
    """Format a human-readable notification text from a lead payload dict."""
    lines = [
        "📬 Новая заявка с etoir.ru",
        "",
        f"Имя: {data['name']}",
        f"Компания: {data['company']}",
        f"Телефон: {data['phone']}",
        f"Email: {data['email']}",
    ]
    if data.get("position"):
        lines.append(f"Должность: {data['position']}")
    if data.get("comment"):
        lines.append(f"Комментарий: {data['comment']}")
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests — verify they PASS**

```bash
cd D:/prod_projects/toir-landing && pytest tests/test_notify.py -v
```

Expected: 4 tests PASSED

### Subtask 1b — `send_telegram`

- [ ] **Step 5: Write failing tests for `send_telegram`**

Append to `tests/test_notify.py`:

```python
import logging


def test_send_telegram_skips_if_no_token(monkeypatch, caplog):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    with caplog.at_level(logging.WARNING, logger="notify"):
        notify.send_telegram("test")
    assert "not set" in caplog.text.lower()


def test_send_telegram_calls_api_with_correct_payload(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:TOKEN")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100999")
    calls = []

    def fake_urlopen(req, timeout=None):
        calls.append({"url": req.full_url, "data": req.data, "timeout": timeout})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    notify.send_telegram("привет")

    assert len(calls) == 1
    assert "123:TOKEN" in calls[0]["url"]
    assert b"\xd0\xbf\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82" in calls[0]["data"]  # "привет" utf-8
    assert calls[0]["timeout"] == 5


def test_send_telegram_swallows_network_error(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:TOKEN")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100999")

    def fail_urlopen(req, timeout=None):
        raise OSError("network down")

    monkeypatch.setattr("urllib.request.urlopen", fail_urlopen)
    notify.send_telegram("test")  # must not raise
```

- [ ] **Step 6: Run tests — verify new tests FAIL**

```bash
cd D:/prod_projects/toir-landing && pytest tests/test_notify.py::test_send_telegram_skips_if_no_token tests/test_notify.py::test_send_telegram_calls_api_with_correct_payload tests/test_notify.py::test_send_telegram_swallows_network_error -v
```

Expected: `AttributeError: module 'notify' has no attribute 'send_telegram'`

- [ ] **Step 7: Implement `send_telegram` — append to `notify.py`**

```python
def send_telegram(text: str) -> None:
    """Send a plain-text message to the configured Telegram chat. Fire-and-forget."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        logger.warning("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set, skipping notification")
        return
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        body = json.dumps({"chat_id": chat_id, "text": text}).encode()
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as exc:
        logger.error("Failed to send Telegram notification: %s", exc)
```

Note: **no `parse_mode`** in the JSON body — plain text only, safe for any user input.

- [ ] **Step 8: Run all notify tests — verify they PASS**

```bash
cd D:/prod_projects/toir-landing && pytest tests/test_notify.py -v
```

Expected: 7 tests PASSED

- [ ] **Step 9: Commit**

```bash
cd D:/prod_projects/toir-landing && git add notify.py tests/test_notify.py && git commit -m "feat: add notify module with build_message and send_telegram"
```

---

## Task 2: Wire `main.py` and patch `tests/test_api.py`

**Files:**
- Modify: `main.py` (line ~73, after `db.save_response(payload)`)
- Modify: `tests/test_api.py` (add autouse fixture)

- [ ] **Step 1: Add `no_telegram` fixture to `tests/test_api.py`**

Add this import at the top of `tests/test_api.py` (after existing imports):

```python
import notify
```

Then add this fixture after the existing `client` fixture:

```python
@pytest.fixture(autouse=True)
def no_telegram(monkeypatch):
    monkeypatch.setattr(notify, "send_telegram", lambda text: None)
```

- [ ] **Step 2: Run existing test_api tests — verify they still PASS**

```bash
cd D:/prod_projects/toir-landing && pytest tests/test_api.py -v
```

Expected: all existing tests PASSED (notify not yet called from main.py, so this just verifies no import errors)

- [ ] **Step 3: Modify `main.py` to call `notify`**

At the top of `main.py`, after the existing imports, add:

```python
import notify
```

In `create_response`, change:

```python
    db.save_response(payload)
    return {"ok": True}
```

to:

```python
    db.save_response(payload)
    notify.send_telegram(notify.build_message(payload))
    return {"ok": True}
```

- [ ] **Step 4: Run all tests — verify everything PASSES**

```bash
cd D:/prod_projects/toir-landing && pytest tests/ -v
```

Expected: all tests PASSED (TG call is monkeypatched to no-op in test_api.py)

- [ ] **Step 5: Commit**

```bash
cd D:/prod_projects/toir-landing && git add main.py tests/test_api.py && git commit -m "feat: send Telegram notification on new lead form submission"
```

---

## Task 3: Update `.env.example`

**Files:**
- Modify: `.env.example`

- [ ] **Step 1: Add TG variables to `.env.example`**

Append to `.env.example`:

```
TELEGRAM_BOT_TOKEN=123456:ABC-your-bot-token
TELEGRAM_CHAT_ID=-100xxxxxxxxxx
```

How to get these values:
1. Create a bot via [@BotFather](https://t.me/BotFather) → get `TELEGRAM_BOT_TOKEN`
2. Add the bot to a channel/group and get the chat ID via `https://api.telegram.org/bot<TOKEN>/getUpdates` → `TELEGRAM_CHAT_ID` (negative number for groups/channels)

- [ ] **Step 2: Commit**

```bash
cd D:/prod_projects/toir-landing && git add .env.example && git commit -m "docs: add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to .env.example"
```
