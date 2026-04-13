import csv
import io
import logging
import os
import secrets
from contextlib import asynccontextmanager
from html import escape

import httpx
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field, field_validator

import db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://etoir.ru", "https://www.etoir.ru"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

security = HTTPBasic()

ADMIN_USER = os.environ["ADMIN_USER"]
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "")


class ResponseIn(BaseModel):
    name: str = Field(max_length=200)
    company: str = Field(max_length=200)
    email: str = Field(max_length=254)
    phone: str = Field(max_length=30)
    position: str | None = Field(default=None, max_length=200)
    comment: str | None = Field(default=None, max_length=2000)
    consent_privacy: bool
    consent_marketing: bool = False

    @field_validator("consent_privacy")
    @classmethod
    def must_be_true(cls, v: bool) -> bool:
        if not v:
            raise ValueError("consent_privacy must be accepted")
        return v


def _verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    ok = secrets.compare_digest(credentials.username, ADMIN_USER) and \
         secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not ok:
        raise HTTPException(
            status_code=401,
            headers={"WWW-Authenticate": "Basic"},
        )


def _send_tg(data: ResponseIn, created_at: str) -> None:
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return
    marketing = "✅" if data.consent_marketing else "❌"
    text = (
        f"📋 Новая заявка\n\n"
        f"Имя: {data.name}\n"
        f"Компания: {data.company}\n"
        f"Email: {data.email}\n"
        f"Телефон: {data.phone}\n"
        f"Должность: {data.position or '—'}\n"
        f"Комментарий: {data.comment or '—'}\n\n"
        f"Дата: {created_at}\n"
        f"Согласие на рассылку: {marketing}"
    )
    try:
        with httpx.Client(timeout=10) as client:
            client.post(
                f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
                json={"chat_id": TG_CHAT_ID, "text": text},
            )
    except Exception as e:
        logger.error("TG notification failed: %s", e)


@app.post("/api/responses/")
def create_response(data: ResponseIn, background_tasks: BackgroundTasks):
    from datetime import datetime, timezone
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    db.save_response(
        data.name, data.company, data.email, data.phone,
        data.position, data.comment,
        data.consent_privacy, data.consent_marketing,
    )
    background_tasks.add_task(_send_tg, data, created_at)
    return {"ok": True}


@app.get("/admin/", response_class=HTMLResponse)
def admin(_=Depends(_verify_admin)):
    rows = db.get_all_responses()
    rows_html = "".join(
        f"<tr><td>{r['id']}</td><td>{r['created_at']}</td><td>{escape(r['name'])}</td>"
        f"<td>{escape(r['company'])}</td><td>{escape(r['email'])}</td><td>{escape(r['phone'])}</td>"
        f"<td>{escape(r.get('position') or '')}</td><td>{escape(r.get('comment') or '')}</td>"
        f"<td>{'✅' if r.get('consent_privacy') else '❌'}</td>"
        f"<td>{'✅' if r.get('consent_marketing') else '❌'}</td></tr>"
        for r in rows
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Заявки</title></head><body>
<h1>Заявки ({len(rows)})</h1>
<p><a href="/admin/export.csv">Скачать CSV</a></p>
<table border="1" cellpadding="4" cellspacing="0">
<tr><th>#</th><th>Дата</th><th>Имя</th><th>Компания</th>
<th>Email</th><th>Телефон</th><th>Должность</th><th>Комментарий</th>
<th>Политика</th><th>Рассылка</th></tr>
{rows_html}
</table></body></html>"""


@app.get("/admin/export.csv")
def export_csv(_=Depends(_verify_admin)):
    rows = db.get_all_responses()
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["id", "created_at", "name", "company",
                    "email", "phone", "position", "comment",
                    "consent_privacy", "consent_marketing"],
    )
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": "attachment; filename=responses.csv"},
    )
