"""Tests for the blog CMS (api/blog.py + api/main.py blog routes).

The active backend lives in ``api/`` (root main.py/db.py are reference copies),
so we put the api directory first on sys.path before importing.
"""
import importlib.util
import os
import sys

API_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "api"))
if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)

os.environ.setdefault("ADMIN_USER", "testadmin")
os.environ.setdefault("ADMIN_PASSWORD", "testpass")

import pytest
from fastapi.testclient import TestClient


def _load(name, filename):
    """Load a module from api/ under ``name`` so cross-imports resolve to api/."""
    spec = importlib.util.spec_from_file_location(name, os.path.join(API_DIR, filename))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# Force the active api/ modules into sys.modules (root main.py/db.py are stale copies).
blog = _load("blog", "blog.py")
db = _load("db", "db.py")
main = _load("main", "main.py")

AUTH = ("testadmin", "testpass")


# ── Pure functions ────────────────────────────────────────────────────────
def test_slugify_transliterates_russian():
    assert blog.slugify("Как внедрить ТОиР-систему") == "kak-vnedrit-toir-sistemu"


def test_slugify_strips_punctuation_and_collapses_dashes():
    assert blog.slugify("  Привет,   мир!!! ") == "privet-mir"


def test_unique_slug_resolves_collision():
    existing = {"cmms-vs-excel", "cmms-vs-excel-2"}
    assert blog.unique_slug("CMMS vs Excel", existing) == "cmms-vs-excel-3"


def test_unique_slug_keeps_current():
    existing = {"my-post"}
    assert blog.unique_slug("My Post", existing, current="my-post") == "my-post"


def test_reading_minutes_rounds_up_minimum_one():
    assert blog.reading_minutes(0) == 1
    assert blog.reading_minutes(181) == 2


def test_replace_between_replaces_payload():
    text = "a<!--S-->old<!--E-->b"
    out = blog.replace_between(text, "<!--S-->", "<!--E-->", "NEW")
    assert "NEW" in out and "old" not in out
    assert out.startswith("a<!--S-->") and out.endswith("<!--E-->b")


def test_replace_between_missing_markers_raises():
    with pytest.raises(ValueError):
        blog.replace_between("no markers here", "<!--S-->", "<!--E-->", "x")


def _sample_article(**over):
    base = {
        "slug": "test-post",
        "kind": "post",
        "status": "published",
        "title": "Тестовая статья про ТОиР",
        "seo_title": None,
        "meta_description": None,
        "excerpt": "Короткое описание статьи.",
        "category": "Внедрение",
        "keywords": "ТОиР, CMMS",
        "lead": "Вводный абзац.",
        "quick_answer": "Быстрый ответ.",
        "hero_image": "/blog/test-post/img/hero.webp",
        "hero_alt": "Иллюстрация",
        "hero_caption": None,
        "content_html": "<h2>Раздел</h2><p>Текст " + "слово " * 200 + "</p>",
        "faq_json": '[{"q": "Вопрос?", "a": "Ответ."}]',
        "published_at": "2026-05-26T10:00:00+00:00",
        "created_at": "2026-05-26T10:00:00+00:00",
        "updated_at": "2026-05-26T10:00:00+00:00",
        "reading_minutes": None,
    }
    base.update(over)
    return base


def test_render_article_includes_core_seo():
    html = blog.render_article(_sample_article())
    assert '<link rel="canonical" href="https://etoir.ru/blog/test-post/">' in html
    assert 'property="og:type" content="article"' in html
    assert '"@type": "Article"' in html
    assert '"@type": "BreadcrumbList"' in html
    assert '"@type": "FAQPage"' in html  # faqs present
    assert "Тестовая статья про ТОиР" in html


def test_render_article_no_faq_block_when_empty():
    html = blog.render_article(_sample_article(faq_json="[]"))
    assert '"@type": "FAQPage"' not in html


def test_render_article_falls_back_to_default_og_image():
    html = blog.render_article(_sample_article(hero_image=None))
    assert "https://etoir.ru/images/og-image.png" in html


def test_build_sitemap_entries_contains_slug():
    out = blog.build_sitemap_entries([{"slug": "abc", "published_at": "2026-05-26T00:00:00+00:00"}])
    assert "https://etoir.ru/blog/abc/" in out
    assert "<lastmod>2026-05-26</lastmod>" in out


# ── Endpoint tests ────────────────────────────────────────────────────────
@pytest.fixture
def app(tmp_path):
    # Other test modules put the repo root first on sys.path and call
    # importlib.reload(main), which re-resolves "main"/"db" to the stale root
    # copies. Re-load the api/ modules by explicit path to heal that.
    global blog, db, main
    blog = _load("blog", "blog.py")
    db = _load("db", "db.py")
    main = _load("main", "main.py")
    landing = tmp_path / "landing"
    (landing / "blog").mkdir(parents=True)
    (landing / "blog" / "index.html").write_text(
        '<div class="blog-grid">\n<!-- BLOG:CARDS:START -->\nOLD\n<!-- BLOG:CARDS:END -->\n</div>\n'
        '<!-- BLOG:ITEMLIST:START -->\nOLD\n<!-- BLOG:ITEMLIST:END -->\n',
        encoding="utf-8",
    )
    (landing / "sitemap.xml").write_text(
        '<urlset>\n<!-- BLOG:SITEMAP:START -->\nOLD\n<!-- BLOG:SITEMAP:END -->\n</urlset>\n',
        encoding="utf-8",
    )
    (landing / "rss.xml").write_text(
        '<rss>\n<!-- BLOG:RSS:START -->\nOLD\n<!-- BLOG:RSS:END -->\n</rss>\n',
        encoding="utf-8",
    )
    db.DB_PATH = str(tmp_path / "test.db")
    main.LANDING_DIR = str(landing)
    db.init_db()
    return main, str(landing)


@pytest.fixture
def client(app):
    m, _ = app
    return TestClient(m.app)


def test_auth_required(client):
    assert client.get("/admin/blog/api/articles").status_code == 401


def test_legacy_seeded_and_listed(client):
    r = client.get("/admin/blog/api/articles", auth=AUTH)
    assert r.status_code == 200
    slugs = {a["slug"] for a in r.json()}
    assert "cmms-vs-excel" in slugs
    assert all(a["kind"] == "legacy" for a in r.json())


def test_create_publish_writes_files(client, app):
    _, landing = app
    create = client.post("/admin/blog/api/articles", auth=AUTH, json={
        "title": "Новая статья про надёжность",
        "excerpt": "Описание.",
        "category": "Аналитика",
        "content_html": "<h2>Заголовок</h2><p>Тело статьи.</p>",
    })
    assert create.status_code == 200
    data = create.json()
    assert data["slug"] == "novaya-statya-pro-nadezhnost"

    pub = client.post(f"/admin/blog/api/articles/{data['id']}/publish", auth=AUTH)
    assert pub.status_code == 200

    article_file = os.path.join(landing, "blog", data["slug"], "index.html")
    assert os.path.exists(article_file)
    html = open(article_file, encoding="utf-8").read()
    assert "Новая статья про надёжность" in html
    assert 'rel="canonical"' in html

    # shared files regenerated between markers
    idx = open(os.path.join(landing, "blog", "index.html"), encoding="utf-8").read()
    assert "Новая статья про надёжность" in idx
    assert "OLD" not in idx
    sm = open(os.path.join(landing, "sitemap.xml"), encoding="utf-8").read()
    assert data["slug"] in sm


def test_unpublish_removes_file(client, app):
    _, landing = app
    cid = client.post("/admin/blog/api/articles", auth=AUTH, json={
        "title": "Черновик статьи", "content_html": "<p>x</p>",
    }).json()["id"]
    slug = client.get(f"/admin/blog/api/articles/{cid}", auth=AUTH).json()["slug"]
    client.post(f"/admin/blog/api/articles/{cid}/publish", auth=AUTH)
    path = os.path.join(landing, "blog", slug, "index.html")
    assert os.path.exists(path)
    client.post(f"/admin/blog/api/articles/{cid}/unpublish", auth=AUTH)
    assert not os.path.exists(path)


def test_cannot_edit_legacy(client):
    legacy = next(a for a in client.get("/admin/blog/api/articles", auth=AUTH).json()
                  if a["kind"] == "legacy")
    r = client.put(f"/admin/blog/api/articles/{legacy['id']}", auth=AUTH,
                   json={"title": "hacked"})
    assert r.status_code == 400


def test_content_is_sanitized(client):
    cid = client.post("/admin/blog/api/articles", auth=AUTH, json={
        "title": "XSS тест",
        "content_html": "<p>ok</p><script>alert(1)</script>",
    }).json()["id"]
    stored = client.get(f"/admin/blog/api/articles/{cid}", auth=AUTH).json()
    assert "<script>" not in stored["content_html"]
    assert "ok" in stored["content_html"]


# ── IndexNow (Yandex) ─────────────────────────────────────────────────────
def test_indexnow_keyfile_created(app):
    main_mod, landing = app
    main_mod.INDEXNOW_KEY = "testkey123"
    try:
        main_mod._ensure_indexnow_keyfile()
        p = os.path.join(landing, "testkey123.txt")
        assert os.path.exists(p)
        assert open(p, encoding="utf-8").read() == "testkey123"
    finally:
        main_mod.INDEXNOW_KEY = ""


def test_ping_indexnow_noop_without_key(app):
    main_mod, _ = app
    main_mod.INDEXNOW_KEY = ""
    # returns immediately without any network attempt
    main_mod._ping_indexnow(["https://etoir.ru/blog/x/"])


def test_publish_pings_indexnow(client, app, monkeypatch):
    main_mod, _ = app
    calls = []
    monkeypatch.setattr(main_mod, "_ping_indexnow", lambda urls: calls.append(urls))
    cid = client.post("/admin/blog/api/articles", auth=AUTH, json={
        "title": "Пинг тест", "content_html": "<p>x</p>",
    }).json()["id"]
    client.post(f"/admin/blog/api/articles/{cid}/publish", auth=AUTH)
    assert calls == [["https://etoir.ru/blog/ping-test/"]]
