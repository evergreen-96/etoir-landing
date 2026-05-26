import csv
import io
import json
import logging
import os
import re
import secrets
import shutil
from contextlib import asynccontextmanager
from html import escape

import httpx
from fastapi import (BackgroundTasks, Depends, FastAPI, File, Form, HTTPException,
                     UploadFile)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field, field_validator

import blog
import db

logger = logging.getLogger(__name__)

HERE = os.path.dirname(os.path.abspath(__file__))
LANDING_DIR = os.environ.get("LANDING_DIR", "/landing")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    _ensure_indexnow_keyfile()
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
# IndexNow (Yandex/Bing fast recrawl). Disabled if no key is configured.
INDEXNOW_KEY = os.environ.get("INDEXNOW_KEY", "")
INDEXNOW_HOST = os.environ.get("SITE_HOST", "etoir.ru")


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
<p><a href="/admin/blog/">📝 Блог-редактор</a> · <a href="/admin/export.csv">Скачать CSV</a></p>
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


# ---------------------------------------------------------------------------
# Blog CMS
# ---------------------------------------------------------------------------
class FaqItem(BaseModel):
    q: str = ""
    a: str = ""


class ArticleIn(BaseModel):
    title: str = Field(default="", max_length=300)
    slug: str | None = Field(default=None, max_length=200)
    seo_title: str | None = Field(default=None, max_length=300)
    meta_description: str | None = Field(default=None, max_length=400)
    excerpt: str | None = Field(default=None, max_length=600)
    category: str | None = Field(default=None, max_length=100)
    keywords: str | None = Field(default=None, max_length=400)
    lead: str | None = Field(default=None, max_length=2000)
    quick_answer: str | None = Field(default=None, max_length=2000)
    hero_image: str | None = Field(default=None, max_length=300)
    hero_alt: str | None = Field(default=None, max_length=400)
    hero_caption: str | None = Field(default=None, max_length=400)
    content_html: str | None = None
    faqs: list[FaqItem] | None = None
    read_also: list | None = None


def _related(slug: str) -> list[dict]:
    return [a for a in db.list_published() if a["slug"] != slug][:3]


def _article_dir(slug: str) -> str:
    return os.path.join(LANDING_DIR, "blog", slug)


def _to_row(data: ArticleIn, existing_slug: str | None = None) -> dict:
    """Build a db-ready dict from an ArticleIn payload (sanitises body, derives slug)."""
    row: dict = data.model_dump(exclude={"faqs", "read_also", "slug"})
    if data.content_html is not None:
        row["content_html"] = blog.sanitize_html(data.content_html)
    if data.faqs is not None:
        row["faq_json"] = json.dumps([f.model_dump() for f in data.faqs], ensure_ascii=False)
    if data.read_also is not None:
        row["read_also_json"] = json.dumps(data.read_also, ensure_ascii=False)
    # slug: explicit value, else from title; ensure unique
    desired = data.slug or existing_slug or data.title
    row["slug"] = blog.unique_slug(desired, db.existing_slugs(), current=existing_slug)
    # word count / reading time
    words = blog.word_count(row.get("content_html"), data.lead, data.quick_answer)
    row["word_count"] = words
    row["reading_minutes"] = blog.reading_minutes(words)
    return row


def _write_article_file(article: dict) -> None:
    if article.get("kind") == "legacy":
        return  # never overwrite hand-built legacy files
    d = _article_dir(article["slug"])
    os.makedirs(d, exist_ok=True)
    html = blog.render_article(article, _related(article["slug"]))
    with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)


def _regen_shared() -> None:
    blog.regenerate_shared(LANDING_DIR, db.list_published())


def _ensure_indexnow_keyfile() -> None:
    """Publish the IndexNow key file at the site root so engines can verify it."""
    if not INDEXNOW_KEY:
        return
    try:
        path = os.path.join(LANDING_DIR, f"{INDEXNOW_KEY}.txt")
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(INDEXNOW_KEY)
    except Exception as e:
        logger.error("IndexNow keyfile error: %s", e)


def _ping_indexnow(urls: list[str]) -> None:
    """Notify Yandex/Bing (IndexNow) about new or updated URLs. No-op without a key."""
    if not INDEXNOW_KEY or not urls:
        return
    payload = {
        "host": INDEXNOW_HOST,
        "key": INDEXNOW_KEY,
        "keyLocation": f"https://{INDEXNOW_HOST}/{INDEXNOW_KEY}.txt",
        "urlList": urls,
    }
    try:
        with httpx.Client(timeout=10) as client:
            client.post("https://yandex.com/indexnow", json=payload,
                        headers={"Content-Type": "application/json; charset=utf-8"})
    except Exception as e:
        logger.error("IndexNow ping failed: %s", e)


def _article_url(slug: str) -> str:
    return f"https://{INDEXNOW_HOST}/blog/{slug}/"


def _require_article(article_id: int) -> dict:
    a = db.get_article(article_id)
    if not a:
        raise HTTPException(status_code=404, detail="article not found")
    return a


@app.get("/admin/blog/", response_class=HTMLResponse)
def blog_editor(_=Depends(_verify_admin)):
    return FileResponse(os.path.join(HERE, "static", "admin_blog.html"))


@app.get("/admin/blog/api/articles")
def blog_list(_=Depends(_verify_admin)):
    return db.list_articles()


@app.get("/admin/blog/api/articles/{article_id}")
def blog_get(article_id: int, _=Depends(_verify_admin)):
    return _require_article(article_id)


@app.post("/admin/blog/api/articles")
def blog_create(data: ArticleIn, _=Depends(_verify_admin)):
    row = _to_row(data)
    row.setdefault("status", "draft")
    row["kind"] = "post"
    new_id = db.create_article(row)
    return {"id": new_id, "slug": row["slug"]}


@app.put("/admin/blog/api/articles/{article_id}")
def blog_update(article_id: int, data: ArticleIn, background_tasks: BackgroundTasks,
                _=Depends(_verify_admin)):
    existing = _require_article(article_id)
    if existing.get("kind") == "legacy":
        raise HTTPException(status_code=400, detail="legacy articles are file-managed")
    row = _to_row(data, existing_slug=existing["slug"])
    db.update_article(article_id, row)
    updated = db.get_article(article_id)
    if updated["status"] == "published":
        # slug may have changed: remove stale dir
        if updated["slug"] != existing["slug"]:
            shutil.rmtree(_article_dir(existing["slug"]), ignore_errors=True)
        _write_article_file(updated)
        _regen_shared()
        background_tasks.add_task(_ping_indexnow, [_article_url(updated["slug"])])
    return {"id": article_id, "slug": updated["slug"]}


@app.post("/admin/blog/api/articles/{article_id}/publish")
def blog_publish(article_id: int, background_tasks: BackgroundTasks,
                 _=Depends(_verify_admin)):
    a = _require_article(article_id)
    if a.get("kind") == "legacy":
        raise HTTPException(status_code=400, detail="legacy articles are file-managed")
    db.set_status(article_id, "published")
    a = db.get_article(article_id)
    _write_article_file(a)
    _regen_shared()
    background_tasks.add_task(_ping_indexnow, [_article_url(a["slug"])])
    return {"ok": True, "url": f"/blog/{a['slug']}/"}


@app.post("/admin/blog/api/articles/{article_id}/unpublish")
def blog_unpublish(article_id: int, _=Depends(_verify_admin)):
    a = _require_article(article_id)
    db.set_status(article_id, "draft")
    index = os.path.join(_article_dir(a["slug"]), "index.html")
    if os.path.exists(index):
        os.remove(index)
    _regen_shared()
    return {"ok": True}


@app.delete("/admin/blog/api/articles/{article_id}")
def blog_delete(article_id: int, _=Depends(_verify_admin)):
    a = _require_article(article_id)
    if a.get("kind") != "legacy":
        shutil.rmtree(_article_dir(a["slug"]), ignore_errors=True)
    db.delete_article(article_id)
    _regen_shared()
    return {"ok": True}


@app.get("/admin/blog/preview/{article_id}", response_class=HTMLResponse)
def blog_preview(article_id: int, _=Depends(_verify_admin)):
    a = _require_article(article_id)
    return blog.render_article(a, _related(a["slug"]))


_ALLOWED_IMG = {"jpg", "jpeg", "png", "webp", "gif", "svg"}


@app.post("/admin/blog/api/upload")
async def blog_upload(article_id: int = Form(...), file: UploadFile = File(...),
                      _=Depends(_verify_admin)):
    a = _require_article(article_id)
    ext = (os.path.splitext(file.filename or "")[1] or "").lower().lstrip(".")
    if ext not in _ALLOWED_IMG:
        raise HTTPException(status_code=400, detail="unsupported image type")
    raw = await file.read()
    data, out_ext = blog.optimize_image(raw, file.filename or "image")
    img_dir = os.path.join(_article_dir(a["slug"]), "img")
    os.makedirs(img_dir, exist_ok=True)
    stem = blog.slugify(os.path.splitext(file.filename or "image")[0]) or "image"
    name = f"{stem}.{out_ext}"
    i = 2
    while os.path.exists(os.path.join(img_dir, name)):
        name = f"{stem}-{i}.{out_ext}"
        i += 1
    with open(os.path.join(img_dir, name), "wb") as f:
        f.write(data)
    return {"location": f"/blog/{a['slug']}/img/{name}"}
