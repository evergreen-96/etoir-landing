"""
main.py — FastAPI-приложение для сбора заявок с лендинга etoir.ru.
"""
import csv
import io
import os
import secrets

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

import db

# ── Инициализация ─────────────────────────────────────────────────────────────

db.init_db()

app = FastAPI(docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://etoir.ru", "https://www.etoir.ru"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

security = HTTPBasic()

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")


# ── Auth ──────────────────────────────────────────────────────────────────────

def require_admin(credentials: HTTPBasicCredentials = Depends(security)):
    ok = secrets.compare_digest(credentials.username, ADMIN_USER) and \
         secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# ── Схемы ─────────────────────────────────────────────────────────────────────

class ResponseIn(BaseModel):
    name:     str
    company:  str
    email:    str
    phone:    str
    position: str | None = None
    comment:  str | None = None


# ── Эндпоинты ─────────────────────────────────────────────────────────────────

@app.post("/api/responses/")
def create_response(data: ResponseIn):
    db.save_response(data.model_dump())
    return {"ok": True}


@app.get("/admin/", response_class=HTMLResponse)
def admin_page(_: str = Depends(require_admin)):
    rows = db.get_all_responses()
    rows_html = ""
    for r in rows:
        rows_html += (
            f"<tr>"
            f"<td>{r['id']}</td>"
            f"<td>{r['created_at'][:16].replace('T', ' ')}</td>"
            f"<td>{_esc(r['name'])}</td>"
            f"<td>{_esc(r['company'])}</td>"
            f"<td>{_esc(r['email'])}</td>"
            f"<td>{_esc(r['phone'])}</td>"
            f"<td>{_esc(r['position'] or '')}</td>"
            f"<td>{_esc(r['comment'] or '')}</td>"
            f"</tr>"
        )
    return f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="UTF-8">
<title>Заявки — etoir.ru</title>
<style>
  body {{ font-family: sans-serif; padding: 2rem; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
  th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
  th {{ background: #f5f5f5; }}
  tr:hover {{ background: #fafafa; }}
  .export {{ margin-bottom: 1rem; }}
  a.btn {{ background: #2563eb; color: #fff; padding: 6px 14px;
           border-radius: 6px; text-decoration: none; font-size: 13px; }}
</style></head>
<body>
<h2>Заявки с etoir.ru ({len(rows)})</h2>
<p class="export"><a class="btn" href="/admin/export.csv">Скачать CSV</a></p>
<table>
<thead><tr>
  <th>#</th><th>Дата</th><th>Имя</th><th>Компания</th>
  <th>Email</th><th>Телефон</th><th>Должность</th><th>Комментарий</th>
</tr></thead>
<tbody>{rows_html}</tbody>
</table>
</body></html>"""


@app.get("/admin/export.csv")
def export_csv(_: str = Depends(require_admin)):
    rows = db.get_all_responses()
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=["id", "created_at", "name", "company", "email",
                    "phone", "position", "comment"],
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(rows)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=responses.csv"},
    )


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
