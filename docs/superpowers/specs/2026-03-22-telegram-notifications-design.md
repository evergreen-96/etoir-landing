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
- Makes a synchronous POST to `https://api.telegram.org/bot{token}/sendMessage` using `urllib` (stdlib, no new dependencies).
- Wraps the call in `try/except Exception` — any error is logged via `logging.error` and swallowed.

### Change: `main.py`

In `create_response`, after `db.save_response(payload)`, call:

```python
notify.send_telegram(build_message(data))
```

where `build_message` formats the notification text (see below).

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

## Out of Scope

- Retries on failure
- Async notification
- Multiple chat targets
- Bot command handling
