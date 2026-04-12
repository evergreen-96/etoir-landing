import csv
import io
import os
import secrets
from contextlib import asynccontextmanager
from html import escape

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field

import db


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


class ResponseIn(BaseModel):
    name: str = Field(max_length=200)
    company: str = Field(max_length=200)
    email: str = Field(max_length=254)
    phone: str = Field(max_length=30)
    position: str | None = Field(default=None, max_length=200)
    comment: str | None = Field(default=None, max_length=2000)


def _verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    ok = secrets.compare_digest(credentials.username, ADMIN_USER) and \
         secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not ok:
        raise HTTPException(
            status_code=401,
            headers={"WWW-Authenticate": "Basic"},
        )


@app.post("/api/responses/")
def create_response(data: ResponseIn):
    db.save_response(
        data.name, data.company, data.email, data.phone,
        data.position, data.comment,
    )
    return {"ok": True}


@app.get("/admin/", response_class=HTMLResponse)
def admin(_=Depends(_verify_admin)):
    rows = db.get_all_responses()
    rows_html = "".join(
        f"<tr><td>{r['id']}</td><td>{r['created_at']}</td><td>{escape(r['name'])}</td>"
        f"<td>{escape(r['company'])}</td><td>{escape(r['email'])}</td><td>{escape(r['phone'])}</td>"
        f"<td>{escape(r.get('position') or '')}</td><td>{escape(r.get('comment') or '')}</td></tr>"
        for r in rows
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Заявки</title></head><body>
<h1>Заявки ({len(rows)})</h1>
<p><a href="/admin/export.csv">Скачать CSV</a></p>
<table border="1" cellpadding="4" cellspacing="0">
<tr><th>#</th><th>Дата</th><th>Имя</th><th>Компания</th>
<th>Email</th><th>Телефон</th><th>Должность</th><th>Комментарий</th></tr>
{rows_html}
</table></body></html>"""


@app.get("/admin/export.csv")
def export_csv(_=Depends(_verify_admin)):
    rows = db.get_all_responses()
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["id", "created_at", "name", "company",
                    "email", "phone", "position", "comment"],
    )
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": "attachment; filename=responses.csv"},
    )
