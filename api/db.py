import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

DB_PATH = os.environ.get("DB_PATH", "/data/responses.db")

# Article columns the API accepts / stores (excludes id and server-managed timestamps).
ARTICLE_FIELDS = [
    "slug", "kind", "status", "title", "seo_title", "meta_description",
    "excerpt", "category", "keywords", "lead", "quick_answer",
    "hero_image", "hero_alt", "hero_caption", "content_html",
    "faq_json", "read_also_json", "reading_minutes", "word_count",
]


def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                name              TEXT NOT NULL,
                company           TEXT NOT NULL,
                email             TEXT NOT NULL,
                phone             TEXT NOT NULL,
                position          TEXT,
                comment           TEXT,
                created_at        TEXT NOT NULL,
                consent_privacy   INTEGER NOT NULL DEFAULT 1,
                consent_marketing INTEGER NOT NULL DEFAULT 0
            )
        """)
        # migrate existing DB
        for col, default in [("consent_privacy", 1), ("consent_marketing", 0)]:
            try:
                conn.execute(f"ALTER TABLE responses ADD COLUMN {col} INTEGER NOT NULL DEFAULT {default}")
            except Exception:
                pass

        conn.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                slug             TEXT NOT NULL UNIQUE,
                kind             TEXT NOT NULL DEFAULT 'post',
                status           TEXT NOT NULL DEFAULT 'draft',
                title            TEXT NOT NULL DEFAULT '',
                seo_title        TEXT,
                meta_description TEXT,
                excerpt          TEXT,
                category         TEXT,
                keywords         TEXT,
                lead             TEXT,
                quick_answer     TEXT,
                hero_image       TEXT,
                hero_alt         TEXT,
                hero_caption     TEXT,
                content_html     TEXT,
                faq_json         TEXT,
                read_also_json   TEXT,
                reading_minutes  INTEGER DEFAULT 1,
                word_count       INTEGER DEFAULT 0,
                created_at       TEXT NOT NULL,
                published_at     TEXT,
                updated_at       TEXT NOT NULL
            )
        """)
    seed_legacy()


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Responses (lead form)
# ---------------------------------------------------------------------------
def save_response(name, company, email, phone, position, comment,
                  consent_privacy: bool = True, consent_marketing: bool = False):
    created_at = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO responses "
            "(name, company, email, phone, position, comment, created_at, "
            "consent_privacy, consent_marketing) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (name, company, email, phone, position, comment, created_at,
             int(consent_privacy), int(consent_marketing)),
        )


def get_all_responses():
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM responses ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Articles (blog CMS)
# ---------------------------------------------------------------------------
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def existing_slugs() -> set[str]:
    with _connect() as conn:
        return {r["slug"] for r in conn.execute("SELECT slug FROM articles").fetchall()}


def create_article(data: dict) -> int:
    now = _now()
    fields = {k: data.get(k) for k in ARTICLE_FIELDS}
    fields["created_at"] = now
    fields["updated_at"] = now
    if fields.get("status") == "published":
        fields["published_at"] = data.get("published_at") or now
    cols = ", ".join(fields.keys())
    qs = ", ".join("?" for _ in fields)
    with _connect() as conn:
        cur = conn.execute(
            f"INSERT INTO articles ({cols}) VALUES ({qs})", tuple(fields.values())
        )
        return cur.lastrowid


def update_article(article_id: int, data: dict) -> None:
    sets = {k: data[k] for k in ARTICLE_FIELDS if k in data}
    sets["updated_at"] = _now()
    if data.get("status") == "published" and not data.get("published_at"):
        existing = get_article(article_id)
        if existing and not existing.get("published_at"):
            sets["published_at"] = sets["updated_at"]
    if "published_at" in data and data["published_at"]:
        sets["published_at"] = data["published_at"]
    assignments = ", ".join(f"{k} = ?" for k in sets)
    with _connect() as conn:
        conn.execute(
            f"UPDATE articles SET {assignments} WHERE id = ?",
            (*sets.values(), article_id),
        )


def set_status(article_id: int, status: str) -> None:
    sets = {"status": status, "updated_at": _now()}
    if status == "published":
        existing = get_article(article_id)
        if existing and not existing.get("published_at"):
            sets["published_at"] = sets["updated_at"]
    assignments = ", ".join(f"{k} = ?" for k in sets)
    with _connect() as conn:
        conn.execute(
            f"UPDATE articles SET {assignments} WHERE id = ?",
            (*sets.values(), article_id),
        )


def get_article(article_id: int) -> dict | None:
    with _connect() as conn:
        r = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
        return dict(r) if r else None


def get_article_by_slug(slug: str) -> dict | None:
    with _connect() as conn:
        r = conn.execute("SELECT * FROM articles WHERE slug = ?", (slug,)).fetchone()
        return dict(r) if r else None


def list_articles() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM articles ORDER BY COALESCE(published_at, created_at) DESC, id DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def list_published() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM articles WHERE status = 'published' "
            "ORDER BY COALESCE(published_at, created_at) DESC, id DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def delete_article(article_id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM articles WHERE id = ?", (article_id,))


# Metadata for the hand-built articles currently public, so regenerated
# index/sitemap/rss keep listing them. Their HTML files are left untouched.
_LEGACY = [
    {
        "slug": "kak-vnedrit-toir-sistemu",
        "title": "Как внедрить ТОиР-систему: пошаговый план за 7 шагов",
        "excerpt": "Пошаговый план внедрения CMMS на промышленном предприятии: от аудита оборудования до KPI и обучения слесарей. 7 этапов, 6-8 недель, проверенная методология.",
        "category": "Внедрение", "reading_minutes": 9, "published_at": "2026-05-19T10:00:00+00:00",
    },
    {
        "slug": "grafik-ppr-oborudovaniya-obrazec",
        "title": "График ППР оборудования: образец и как составить в 2026",
        "excerpt": "Что такое график планово-предупредительного ремонта, как составить годовой план-график ППР по шагам и где скачать готовый шаблон в Excel. Виды ремонтов (ТО, текущий, средний, капитальный), расчёт межремонтного цикла с калькулятором, пример графика ППР для станочного парка и сравнение ручного графика с автоматическим в системе ТОиР.",
        "category": "Документы", "reading_minutes": 9, "published_at": "2026-05-27T10:00:00+00:00",
    },
    {
        "slug": "naryad-zakaz-na-remont-oborudovaniya-obrazec",
        "title": "Наряд-заказ на ремонт оборудования: образец 2026 и автоматизация",
        "excerpt": "Что такое наряд-заказ на ремонт оборудования, какие реквизиты обязательны, порядок заполнения и где скачать бланк в Word и Excel. Чем электронный наряд-заказ в CMMS-системе удобнее бумажного: автоматическая нумерация, история по оборудованию, контроль исполнения, фото-отчёты и подписи прямо со смартфона.",
        "category": "Документы", "reading_minutes": 8, "published_at": "2026-05-21T10:00:00+00:00",
    },
    {
        "slug": "cmms-vs-excel",
        "title": "эТОИР vs Excel: почему таблицы больше не работают",
        "excerpt": "Сравнение Excel-таблиц и специализированной CMMS на 8 параметрах: учёт оборудования, расчёт MTBF и MTTR, мобильность для слесарей, аналитика простоев, история ремонтов, контроль запчастей. На каком масштабе парка таблицы перестают тянуть промышленный завод и какие конкретные потери это создаёт.",
        "category": "Сравнение", "reading_minutes": 7, "published_at": "2026-05-19T10:00:00+00:00",
    },
    {
        "slug": "zachem-avtomatizirovat-toir",
        "title": "Зачем автоматизировать ТОиР: 6 причин перейти на эТОИР",
        "excerpt": "Шесть причин, по которым ручной учёт ТОиР обходится производству дороже специализированной системы: незапланированные простои, аварийные ремонты, потери запчастей со склада, выгорание ремонтного персонала, отсутствие аналитики надёжности и невозможность защитить ремонтный бюджет перед финансистами.",
        "category": "Бизнес-кейс", "reading_minutes": 6, "published_at": "2026-05-19T09:00:00+00:00",
    },
]


def seed_legacy() -> None:
    """Insert metadata rows for pre-existing hand-built articles (idempotent)."""
    now = _now()
    with _connect() as conn:
        have = {r["slug"] for r in conn.execute("SELECT slug FROM articles").fetchall()}
        for a in _LEGACY:
            if a["slug"] in have:
                continue
            conn.execute(
                "INSERT INTO articles "
                "(slug, kind, status, title, excerpt, category, reading_minutes, "
                " created_at, published_at, updated_at) "
                "VALUES (?, 'legacy', 'published', ?, ?, ?, ?, ?, ?, ?)",
                (a["slug"], a["title"], a["excerpt"], a["category"],
                 a["reading_minutes"], now, a["published_at"], now),
            )
