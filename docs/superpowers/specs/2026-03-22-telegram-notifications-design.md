# Telegram Notifications — Design Spec

**Date:** 2026-03-22
**Project:** toir-landing (etoir.ru)
**Scope:** Send a Telegram message when a new lead form is submitted.

---

## Problem

New form submissions are saved to SQLite but there is no real-time alerting. The team only learns about leads by checking the admin page manually.

## Goal

When `POST /api/responses/` saves a new response, immediately send a notification to a Telegram chat via a bot. If Telegram is unavailable, the form response still saves successfully (fire-and-forget).

---

## Architecture

### New file: `notify.py`

Single-responsibility module. Exports one function:

```python
def send_telegram(text: str) -> None
```

- Reads `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` from environment variables.
- If either variable is missing, logs a warning and returns silently (allows running without TG configured).
- Makes a synchronous POST to `https://api.telegram.org/bot{token}/sendMessage` using `urllib.request` (stdlib, no new dependencies).
- Request body is JSON-encoded via `json.dumps({"chat_id": ..., "text": ...})`, sent with `Content-Type: application/json`.
- **`parse_mode` must NOT be set** — plain text only. This avoids Telegram parse errors when user-supplied fields contain Markdown/HTML special characters.
- **Timeout: 5 seconds** — `urlopen(req, timeout=5)` to prevent blocking the FastAPI worker thread indefinitely.
- Wraps the call in `try/except Exception` — any error is logged via `logging.error` and swallowed.

Also exports a helper used by `main.py`:

```python
def build_message(data: dict) -> str
```

Accepts the `payload` dict (same shape as `ResponseIn.model_dump()` + `ip_address`). Returns a formatted string. Optional fields (`position`, `comment`) are appended only when non-empty/non-None — never the literal string `"None"`.

### Change: `main.py`

In `create_response`, after `db.save_response(payload)`, call:

```python
notify.send_telegram(notify.build_message(payload))
```

### Change: `.env.example`

Add two new variables:

```
TELEGRAM_BOT_TOKEN=123456:ABC-your-bot-token
TELEGRAM_CHAT_ID=-100xxxxxxxxxx
```

---

## Notification Format

```
📬 Новая заявка с etoir.ru

Имя: {name}
Компания: {company}
Телефон: {phone}
Email: {email}
```

Optional fields (position, comment) are appended if non-empty.

---

## Error Handling

| Scenario | Behavior |
|---|---|
| TG token/chat not configured | Log warning, skip notification |
| Network timeout / TG API error | Log error, skip notification |
| Any other exception | Log error, skip notification |

The HTTP response from `db.save_response` is always `{"ok": True}` regardless of notification outcome.

---

## No New Dependencies

Uses `urllib.request` from the Python standard library. `requirements.txt` is unchanged.

---

## Testing

- In tests, monkeypatch `notify.send_telegram` to a no-op so existing `test_api.py` tests continue passing without a TG token configured and without making real network calls.
- `notify.build_message` can be unit-tested directly with a sample dict.

---

## Out of Scope

- Retries on failure
- Async notification
- Multiple chat targets
- Bot command handling
