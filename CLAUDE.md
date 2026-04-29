# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lead-capture landing page for **etoir.ru** (e-toir SaaS product). Visitors fill a contact form; submissions are saved to SQLite and forwarded to a Telegram chat. An HTTP Basic-auth admin panel at `/admin/` shows all leads with CSV export.

## Architecture

```
nginx (entry point, ports 80/443)
  ├── /              → serves ./landing/ as static files
  ├── /api/          → proxied to FastAPI container (api:8000)
  └── /admin/        → proxied to FastAPI container (api:8000)
```

- **`landing/`** — plain HTML/CSS/JS, no build step. Files are volume-mounted into the nginx container at runtime.
- **`api/`** — the active FastAPI backend. Contains its own `main.py`, `db.py`, `requirements.txt`, and `Dockerfile`.
- **`nginx/`** — nginx configs (`etoir.conf` for production, `etoir-init.conf` for the ACME bootstrap phase).
- **Root `main.py` / `db.py`** — older reference copies; **not used in production**. The canonical code lives in `api/`.

## Common Commands

All infrastructure is managed via Docker Compose through the Makefile:

```bash
make build    # (re)build and start all containers
make up       # start without rebuilding
make down     # stop (prompts for confirmation)
make logs     # tail nginx logs
```

SSL certificate issuance (run once on a fresh server):
```bash
make ssl          # main domains (etoir.ru, www.etoir.ru, e-toir.ru)
make ssl-demo     # demo.e-toir.ru
make ssl-preprod  # preprod.e-toir.ru
```

## Running Tests

Tests are in `tests/` and run against the **root-level** `main.py`/`db.py` (not `api/`). Install dev deps and run from the repo root:

```bash
pip install -r requirements-dev.txt
pytest
pytest tests/test_api.py   # single file
```

## Environment Variables

The API container reads these from `.env` (via `env_file: .env` in `docker-compose.yml`):

| Variable | Required | Description |
|---|---|---|
| `ADMIN_USER` | yes | HTTP Basic auth username for `/admin/` |
| `ADMIN_PASSWORD` | yes | HTTP Basic auth password for `/admin/` |
| `TG_BOT_TOKEN` | no | Telegram bot token for lead notifications |
| `TG_CHAT_ID` | no | Telegram chat/channel ID to receive notifications |

`DB_PATH` is hardcoded to `/data/responses.db` inside the container (Docker volume `responses-data`).

## Data Model

Single SQLite table `responses`:

```
id, name, company, email, phone, position, comment,
created_at (ISO-8601 UTC), consent_privacy (int), consent_marketing (int)
```

`consent_privacy=true` is validated and required by the API. `consent_marketing` defaults to false. Both columns were added via `ALTER TABLE` migration in `db.init_db()` to support existing databases.

## API Endpoints

- `POST /api/responses/` — create a lead; fires Telegram notification as a background task
- `GET /admin/` — HTML table of all leads (Basic auth required)
- `GET /admin/export.csv` — download all leads as CSV (Basic auth required)
