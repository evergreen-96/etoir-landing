"""Blog CMS rendering: slugs, SEO HTML, index/sitemap/rss regeneration.

All functions here are pure (no DB, no network) so they can be unit-tested
directly. File-writing helpers take an explicit ``landing_dir`` argument.
"""
import io
import json
import math
import os
import re
from datetime import datetime, timezone

import bleach
from jinja2 import Template

try:
    from PIL import Image
except Exception:  # Pillow optional at import time (tests of pure funcs)
    Image = None

SITE = "https://etoir.ru"
WORDS_PER_MINUTE = 180

LANDING_DIR = os.environ.get("LANDING_DIR", "/landing")

# ---------------------------------------------------------------------------
# Transliteration / slug
# ---------------------------------------------------------------------------
_TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}

_RU_MONTHS = [
    "", "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]


def slugify(title: str) -> str:
    """Transliterate a (possibly Russian) title into a URL slug."""
    s = (title or "").strip().lower()
    out = []
    for ch in s:
        if ch in _TRANSLIT:
            out.append(_TRANSLIT[ch])
        elif ch.isalnum() and ch.isascii():
            out.append(ch)
        elif ch in " -_":
            out.append("-")
        # everything else dropped
    slug = "".join(out)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "article"


def unique_slug(title: str, existing: set[str], current: str | None = None) -> str:
    """Return a slug for ``title`` not colliding with ``existing`` (minus ``current``)."""
    base = slugify(title)
    taken = set(existing) - ({current} if current else set())
    if base not in taken:
        return base
    i = 2
    while f"{base}-{i}" in taken:
        i += 1
    return f"{base}-{i}"


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------
def strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html or "")


def word_count(*chunks: str) -> int:
    text = " ".join(strip_tags(c) for c in chunks if c)
    words = re.findall(r"\w+", text, flags=re.UNICODE)
    return len(words)


def reading_minutes(words: int) -> int:
    return max(1, math.ceil(words / WORDS_PER_MINUTE))


def ru_date(iso: str) -> str:
    """'2026-05-19' or full ISO -> '19 мая 2026'."""
    if not iso:
        return ""
    d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return f"{d.day} {_RU_MONTHS[d.month]} {d.year}"


def iso_date(iso: str) -> str:
    """Normalise to YYYY-MM-DD."""
    if not iso:
        return ""
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%Y-%m-%d")


def rfc822(iso: str) -> str:
    """ISO -> RFC-822 in +0300 (used by RSS pubDate)."""
    if not iso:
        iso = datetime.now(timezone.utc).isoformat()
    d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    mons = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{days[d.weekday()]}, {d.day:02d} {mons[d.month]} {d.year} 10:00:00 +0300"


# ---------------------------------------------------------------------------
# HTML sanitisation
# ---------------------------------------------------------------------------
ALLOWED_TAGS = [
    "p", "h2", "h3", "h4", "ul", "ol", "li", "strong", "em", "b", "i", "u",
    "a", "img", "figure", "figcaption", "table", "thead", "tbody", "tr", "th",
    "td", "caption", "blockquote", "code", "pre", "br", "hr", "div", "span",
    "details", "summary",
]
ALLOWED_ATTRS = {
    "*": ["class", "id"],
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "width", "height", "loading", "fetchpriority"],
    "th": ["colspan", "rowspan", "scope"],
    "td": ["colspan", "rowspan"],
    "table": ["border"],
}


def sanitize_html(html: str) -> str:
    cleaned = bleach.clean(
        html or "",
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        strip=True,
    )
    return cleaned


# ---------------------------------------------------------------------------
# Image optimisation
# ---------------------------------------------------------------------------
MAX_IMAGE_WIDTH = 1600


def optimize_image(raw: bytes, filename: str) -> tuple[bytes, str]:
    """Return (bytes, extension). Raster -> width-capped WebP; SVG kept as-is."""
    ext = (os.path.splitext(filename)[1] or "").lower().lstrip(".")
    if ext == "svg" or filename.lower().endswith(".svg"):
        return raw, "svg"
    if Image is None:
        return raw, ext or "bin"
    img = Image.open(io.BytesIO(raw))
    if img.mode in ("P", "RGBA", "LA"):
        img = img.convert("RGBA") if "A" in img.mode else img.convert("RGB")
    elif img.mode != "RGB":
        img = img.convert("RGB")
    if img.width > MAX_IMAGE_WIDTH:
        ratio = MAX_IMAGE_WIDTH / img.width
        img = img.resize((MAX_IMAGE_WIDTH, int(img.height * ratio)))
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=82, method=6)
    return buf.getvalue(), "webp"


# ---------------------------------------------------------------------------
# Article HTML template
# ---------------------------------------------------------------------------
_ARTICLE_TMPL = Template(r"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ seo_title }}</title>
    <meta name="description" content="{{ meta_description }}">
    <meta name="robots" content="index, follow, max-image-preview:large">
    <link rel="canonical" href="{{ url }}">

    <!-- Open Graph -->
    <meta property="og:title" content="{{ seo_title }}">
    <meta property="og:description" content="{{ meta_description }}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{{ url }}">
    <meta property="og:image" content="{{ og_image }}">
    <meta property="og:image:alt" content="{{ hero_alt or title }}">
    <meta property="og:locale" content="ru_RU">
    <meta property="og:site_name" content="эТОИР">
    <meta property="article:published_time" content="{{ published }}">
    <meta property="article:modified_time" content="{{ modified }}">
    <meta property="article:author" content="эТОИР">
    <meta property="article:section" content="{{ category }}">
    {% if keywords %}<meta property="article:tag" content="{{ keywords }}">{% endif %}

    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{{ seo_title }}">
    <meta name="twitter:description" content="{{ meta_description }}">
    <meta name="twitter:image" content="{{ og_image }}">
    <meta name="twitter:image:alt" content="{{ hero_alt or title }}">

    {% if hero_image %}<link rel="preload" as="image" href="{{ hero_image }}" fetchpriority="high">{% endif %}
    <link rel="alternate" type="application/rss+xml" title="Блог эТОИР" href="/rss.xml">

    <!-- Yandex.Metrika counter -->
    <script type="text/javascript">
        (function(m,e,t,r,i,k,a){
            m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
            m[i].l=1*new Date();
            for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
            k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
        })(window, document,'script','https://mc.yandex.ru/metrika/tag.js?id=107942912', 'ym');
        ym(107942912, 'init', {
            ssr: true, webvisor: true, clickmap: true,
            ecommerce: 'dataLayer', referrer: document.referrer,
            url: location.href, accurateTrackBounce: true, trackLinks: true
        });
    </script>
    <noscript><div><img src="https://mc.yandex.ru/watch/107942912" style="position:absolute; left:-9999px;" alt=""></div></noscript>
    <!-- /Yandex.Metrika counter -->

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">

    <style>
        :root { --primary:#2563EB; --accent:#F59E0B; --text:#1E293B; --text-secondary:#64748B; --card-bg:#FFFFFF; --border:#E2E8F0; --bg:#FAFBFF; --bg-alt:#F1F5F9; --radius:16px; --card-shadow-hover:0 12px 32px rgba(37,99,235,.12); }
        * { box-sizing:border-box; margin:0; padding:0; }
        html { scroll-behavior:smooth; }
        body { font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif; color:var(--text); background:var(--bg); line-height:1.5; -webkit-font-smoothing:antialiased; }
        a { color:inherit; text-decoration:none; }
        .container { max-width:1200px; margin:0 auto; padding:0 24px; }
        .header { position:sticky; top:0; z-index:100; background:rgba(255,255,255,.92); backdrop-filter:blur(12px); border-bottom:1px solid var(--border); }
        .header-inner { display:flex; align-items:center; justify-content:space-between; padding:16px 0; gap:24px; }
        .brand { font-weight:800; font-size:1.25rem; color:var(--text); letter-spacing:-.01em; }
        .brand span { color:var(--primary); }
        .nav { display:flex; gap:28px; align-items:center; }
        .nav a { color:var(--text); font-weight:500; font-size:.9375rem; transition:color .2s; }
        .nav a:hover { color:var(--primary); }
        .nav a.active { color:var(--primary); font-weight:600; }
        .header-cta { display:inline-block; padding:10px 18px; background:var(--primary); color:#fff; border-radius:10px; font-weight:600; font-size:.9375rem; transition:transform .15s,box-shadow .2s; }
        .header-cta:hover { transform:translateY(-1px); box-shadow:0 8px 20px rgba(37,99,235,.25); }
        @media (max-width:768px){ .nav{display:none;} .header-cta{display:none;} }
        .footer { background:var(--bg-alt); border-top:1px solid var(--border); padding:48px 0 32px; }
        .footer-inner { display:flex; flex-direction:column; align-items:center; gap:20px; text-align:center; }
        .footer-logo { font-weight:800; font-size:1.25rem; color:var(--text); }
        .footer-logo span { color:var(--primary); }
        .footer-links { display:flex; flex-wrap:wrap; justify-content:center; gap:24px; }
        .footer-links a { color:var(--text-secondary); font-size:.9375rem; transition:color .2s; }
        .footer-links a:hover { color:var(--primary); }
        .footer-copy { color:var(--text-secondary); font-size:.875rem; line-height:1.6; }
        .article-layout{max-width:1200px;margin:0 auto;padding:40px 24px;display:grid;grid-template-columns:280px 1fr;gap:48px}
        .article-toc{position:sticky;top:100px;align-self:start;max-height:calc(100vh - 120px);overflow-y:auto;font-size:.9rem}
        .article-toc-title{font-weight:700;margin-bottom:12px;color:var(--text)}
        .article-toc-list{list-style:none;padding:0;margin:0;border-left:2px solid var(--border)}
        .article-toc-list li{padding:6px 0 6px 16px}
        .article-toc-list a{color:var(--text-secondary);text-decoration:none;display:block;transition:color .2s}
        .article-toc-list a:hover{color:var(--primary)}
        .article-toc-list li.active{border-left:2px solid var(--primary);margin-left:-2px}
        .article-toc-list li.active a{color:var(--primary);font-weight:600}
        .article-toc-mobile{display:none;margin:24px 0;padding:16px;background:var(--bg-alt);border-radius:12px}
        .article-toc-mobile summary{cursor:pointer;font-weight:600;color:var(--text)}
        .article-toc-mobile ul{list-style:none;padding:12px 0 0;margin:0}
        .article-toc-mobile li{padding:6px 0}
        .article-toc-mobile a{color:var(--primary);text-decoration:none}
        .breadcrumb{font-size:.875rem;color:var(--text-secondary);margin-bottom:16px}
        .breadcrumb a{color:var(--primary);text-decoration:none}
        .article-content h1{font-size:2.25rem;line-height:1.2;margin:8px 0 12px;color:var(--text)}
        .article-meta{color:var(--text-secondary);font-size:.9rem;margin:0 0 24px}
        .article-lead{font-size:1.125rem;line-height:1.6;color:var(--text);margin-bottom:24px}
        .article-content h2{margin-top:48px;scroll-margin-top:100px;color:var(--text)}
        .article-content h3{margin-top:28px;color:var(--text);font-size:1.125rem}
        .article-content p,.article-content li{line-height:1.7;color:var(--text)}
        .article-content p{margin-bottom:16px}
        .article-content ul,.article-content ol{margin:0 0 20px 24px}
        .article-content li{margin-bottom:8px}
        .article-content a{color:var(--primary)}
        .article-content table{width:100%;border-collapse:collapse;margin:24px 0;font-size:.95rem;background:var(--card-bg);border-radius:8px;overflow:hidden}
        .article-content th,.article-content td{padding:12px 14px;text-align:left;border-bottom:1px solid var(--border)}
        .article-content th{background:var(--bg-alt);font-weight:700}
        .article-content figure{margin:24px 0}
        .article-content figure img{width:100%;height:auto;border-radius:12px;display:block;box-shadow:0 4px 12px rgba(15,23,42,.06)}
        .article-content figcaption{margin-top:8px;font-size:.875rem;color:var(--text-secondary);text-align:center;font-style:italic}
        .quick-answer{background:#EFF6FF;border-left:4px solid var(--primary);padding:16px 20px;border-radius:8px;margin:16px 0 24px;font-size:1rem;line-height:1.6}
        .quick-answer strong{color:var(--primary)}
        .inline-cta{background:linear-gradient(135deg,#EFF6FF 0%,#DBEAFE 100%);border-radius:14px;padding:20px 24px;margin:32px 0;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}
        .inline-cta-text{flex:1;min-width:260px;color:var(--text);font-weight:500}
        .inline-cta a{background:var(--primary);color:#fff;padding:10px 20px;border-radius:10px;font-weight:600;text-decoration:none;white-space:nowrap}
        .read-also{margin-top:48px;padding:24px;background:var(--bg-alt);border-radius:14px}
        .read-also h3{margin-top:0}
        .read-also ul{list-style:none;margin:0;padding:0}
        .read-also li{padding:8px 0;border-bottom:1px solid var(--border)}
        .read-also li:last-child{border-bottom:none}
        .read-also a{color:var(--primary);font-weight:600;text-decoration:none}
        .faq-block details{background:var(--card-bg);border:1px solid var(--border);border-radius:10px;padding:14px 18px;margin-bottom:10px}
        .faq-block summary{cursor:pointer;font-weight:600;color:var(--text);font-size:1rem}
        .faq-block details[open] summary{color:var(--primary);margin-bottom:10px}
        .faq-block p{margin-bottom:0!important;color:var(--text-secondary)}
        .sticky-cta-mobile{display:none;position:fixed;bottom:0;left:0;right:0;height:56px;background:var(--primary);color:#fff;align-items:center;justify-content:space-between;padding:0 16px;z-index:100;transform:translateY(100%);transition:transform .3s ease;box-shadow:0 -4px 12px rgba(0,0,0,.12)}
        .sticky-cta-mobile.visible{transform:translateY(0)}
        .sticky-cta-text{font-size:.875rem;font-weight:500;flex:1;padding-right:12px}
        .sticky-cta-btn{background:var(--accent);color:var(--text);padding:8px 16px;border-radius:8px;font-weight:600;text-decoration:none;font-size:.875rem;white-space:nowrap}
        .sticky-cta-close{background:none;border:none;color:rgba(255,255,255,.7);font-size:18px;padding:0 8px;cursor:pointer}
        @media (max-width:768px){.sticky-cta-mobile{display:flex}}
        @media (max-width:1024px){.article-layout{grid-template-columns:1fr;gap:24px}.article-toc{display:none}.article-toc-mobile{display:block}}
    </style>

    <!-- JSON-LD: Article -->
    <script type="application/ld+json">
    {{ article_jsonld | safe }}
    </script>

    <!-- JSON-LD: Breadcrumbs -->
    <script type="application/ld+json">
    {{ breadcrumb_jsonld | safe }}
    </script>
    {% if faq_jsonld %}
    <!-- JSON-LD: FAQPage -->
    <script type="application/ld+json">
    {{ faq_jsonld | safe }}
    </script>
    {% endif %}
</head>
<body>
    <header class="header" role="banner">
        <div class="container">
            <div class="header-inner">
                <a href="/" class="brand"><span>э</span>ТОИР</a>
                <nav class="nav" role="navigation" aria-label="Основная навигация">
                    <a href="/#features-section">Возможности</a>
                    <a href="/#how-it-works">Как это работает</a>
                    <a href="/#advantages">Преимущества</a>
                    <a href="/blog/" class="active" aria-current="page">Блог</a>
                    <a href="/#faq">FAQ</a>
                </nav>
                <a href="/#contact" class="header-cta">Записаться</a>
            </div>
        </div>
    </header>

    <main class="article-layout" role="main">
        <aside class="article-toc" aria-label="Содержание статьи">
            <div class="article-toc-title">Содержание</div>
            <ul class="article-toc-list"></ul>
        </aside>
        <article class="article-content">
            <nav class="breadcrumb" aria-label="Хлебные крошки">
                <a href="/">Главная</a> →
                <a href="/blog/">Блог</a> →
                <span>{{ title }}</span>
            </nav>

            <h1>{{ title }}</h1>
            <p class="article-meta">Опубликовано <time datetime="{{ published }}">{{ published_ru }}</time>{% if modified and modified != published %} · обновлено <time datetime="{{ modified }}">{{ modified_ru }}</time>{% endif %} · {{ reading_minutes }} мин чтения · автор: эТОИР</p>

            {% if hero_image %}
            <figure>
                <img src="{{ hero_image }}" alt="{{ hero_alt or title }}" loading="eager" fetchpriority="high">
                {% if hero_caption %}<figcaption>{{ hero_caption }}</figcaption>{% endif %}
            </figure>
            {% endif %}

            {% if quick_answer %}
            <p class="quick-answer"><strong>Коротко:</strong> {{ quick_answer }}</p>
            {% endif %}

            {% if lead %}<p class="article-lead">{{ lead }}</p>{% endif %}

            <details class="article-toc-mobile"><summary>📋 Содержание статьи</summary><ul></ul></details>

            {{ content_html | safe }}

            <div class="inline-cta">
                <div class="inline-cta-text">Готовы посмотреть, как ваши процессы выглядят в CMMS? Бесплатное демо 30 минут — покажем на ваших данных.</div>
                <a href="/#contact">Записаться на демо</a>
            </div>

            {% if faqs %}
            <h2 id="faq">Частые вопросы</h2>
            <div class="faq-block">
                {% for f in faqs %}
                <details>
                    <summary>{{ f.q }}</summary>
                    <p>{{ f.a }}</p>
                </details>
                {% endfor %}
            </div>
            {% endif %}

            {% if related %}
            <aside class="read-also" aria-label="Похожие материалы">
                <h3>Читайте также</h3>
                <ul>
                    {% for r in related %}
                    <li><a href="/blog/{{ r.slug }}/">{{ r.title }}</a></li>
                    {% endfor %}
                </ul>
            </aside>
            {% endif %}
        </article>
    </main>

    <div class="sticky-cta-mobile" aria-hidden="true">
        <span class="sticky-cta-text">Бесплатное демо CMMS за 30 минут</span>
        <a href="/#contact" class="sticky-cta-btn">Получить демо</a>
        <button class="sticky-cta-close" aria-label="Закрыть">✕</button>
    </div>

    <footer class="footer" role="contentinfo">
        <div class="container">
            <div class="footer-inner">
                <div class="footer-logo"><span>э</span>ТОИР</div>
                <div class="footer-links">
                    <a href="/#features-section">Возможности</a>
                    <a href="/#advantages">Преимущества</a>
                    <a href="/#faq">FAQ</a>
                    <a href="/blog/">Блог</a>
                    <a href="/#contact">Контакт</a>
                    <a href="/privacy/">Политика конфиденциальности</a>
                </div>
                <div class="footer-copy">
                    &copy; 2026 эТОИР. Все права защищены.
                    <br>Информация на сайте является справочной, не является публичной офертой.
                </div>
            </div>
        </div>
    </footer>

    <script>
    function initToc(){const a=document.querySelector('.article-content');if(!a)return;const hs=a.querySelectorAll('h2');if(!hs.length)return;const dl=document.querySelector('.article-toc-list'),ml=document.querySelector('.article-toc-mobile ul'),ms=document.querySelector('.article-toc-mobile summary');hs.forEach((h,i)=>{if(!h.id)h.id='h2-'+(i+1);const t=h.textContent.trim(),l=`<li data-target="${h.id}"><a href="#${h.id}">${t}</a></li>`;dl&&dl.insertAdjacentHTML('beforeend',l);ml&&ml.insertAdjacentHTML('beforeend',l)});ms&&(ms.textContent=`📋 Содержание (${hs.length} ${hs.length===1?'раздел':'разделов'})`);const ti=document.querySelectorAll('.article-toc-list li'),io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){const id=e.target.id;ti.forEach(li=>li.classList.toggle('active',li.dataset.target===id))}}),{rootMargin:'-80px 0px -70% 0px',threshold:0});hs.forEach(h=>io.observe(h))}
    function initStickyCta(){const c=document.querySelector('.sticky-cta-mobile');if(!c)return;if(sessionStorage.getItem('sticky-cta-dismissed'))return;const a=document.querySelector('.article-content');if(!a)return;const sa=a.offsetTop+a.offsetHeight*.4;let s=!1;window.addEventListener('scroll',()=>{if(s)return;if(window.scrollY+window.innerHeight>=sa){c.classList.add('visible');c.setAttribute('aria-hidden','false');s=!0}},{passive:!0});c.querySelector('.sticky-cta-close').addEventListener('click',()=>{c.classList.remove('visible');c.setAttribute('aria-hidden','true');sessionStorage.setItem('sticky-cta-dismissed','1')});c.querySelector('.sticky-cta-btn').addEventListener('click',()=>{window.ym&&ym(107942912,'reachGoal','sticky_cta_click')})}
    document.addEventListener('DOMContentLoaded',()=>{initToc();initStickyCta()});
    </script>
</body>
</html>
""", autoescape=True)


def render_article(article: dict, related: list[dict] | None = None) -> str:
    """Render a full SEO-optimised article page from a stored article dict."""
    related = related or []
    slug = article["slug"]
    url = f"{SITE}/blog/{slug}/"
    title = article.get("title", "")
    seo_title = article.get("seo_title") or title
    excerpt = article.get("excerpt") or ""
    meta_description = article.get("meta_description") or excerpt
    category = article.get("category") or "Статьи"
    keywords = article.get("keywords") or ""
    hero_image = article.get("hero_image") or ""
    og_image = (SITE + hero_image) if hero_image else f"{SITE}/images/og-image.png"
    published = iso_date(article.get("published_at") or article.get("created_at") or "")
    modified = iso_date(article.get("updated_at") or published)

    faqs = _parse_json_list(article.get("faq_json"))
    content_html = article.get("content_html") or ""
    words = word_count(content_html, article.get("lead"), article.get("quick_answer"))
    reading = article.get("reading_minutes") or reading_minutes(words)

    article_jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": seo_title,
        "description": meta_description,
        "datePublished": published,
        "dateModified": modified,
        "inLanguage": "ru-RU",
        "author": {"@type": "Organization", "name": "эТОИР", "url": SITE},
        "publisher": {
            "@type": "Organization", "name": "эТОИР",
            "logo": {"@type": "ImageObject", "url": f"{SITE}/images/logo.png",
                     "width": "200", "height": "60"},
        },
        "image": {"@type": "ImageObject", "url": og_image},
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "articleSection": category,
        "keywords": keywords,
        "wordCount": str(words),
    }, ensure_ascii=False, indent=2)

    breadcrumb_jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Главная", "item": f"{SITE}/"},
            {"@type": "ListItem", "position": 2, "name": "Блог", "item": f"{SITE}/blog/"},
            {"@type": "ListItem", "position": 3, "name": title, "item": url},
        ],
    }, ensure_ascii=False, indent=2)

    faq_jsonld = ""
    if faqs:
        faq_jsonld = json.dumps({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": f["q"],
                 "acceptedAnswer": {"@type": "Answer", "text": f["a"]}}
                for f in faqs
            ],
        }, ensure_ascii=False, indent=2)

    return _ARTICLE_TMPL.render(
        url=url, title=title, seo_title=seo_title, meta_description=meta_description,
        category=category, keywords=keywords, hero_image=hero_image, og_image=og_image,
        hero_alt=article.get("hero_alt"), hero_caption=article.get("hero_caption"),
        quick_answer=article.get("quick_answer"), lead=article.get("lead"),
        content_html=content_html, faqs=faqs, related=related,
        published=published, modified=modified,
        published_ru=ru_date(published), modified_ru=ru_date(modified),
        reading_minutes=reading,
        article_jsonld=article_jsonld, breadcrumb_jsonld=breadcrumb_jsonld,
        faq_jsonld=faq_jsonld,
    )


def _parse_json_list(raw):
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Marker-based regeneration of shared files
# ---------------------------------------------------------------------------
def replace_between(text: str, start: str, end: str, payload: str) -> str:
    """Replace content between ``start`` and ``end`` markers.

    Raises ValueError if the markers are missing (fail-safe: caller skips write).
    """
    s = text.find(start)
    e = text.find(end)
    if s == -1 or e == -1 or e < s:
        raise ValueError(f"markers {start!r}/{end!r} not found")
    return text[: s + len(start)] + "\n" + payload + "\n" + text[e:]


def _esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build_index_cards(articles: list[dict]) -> str:
    cards = []
    for a in articles:
        meta = f'{ru_date(a.get("published_at") or a.get("created_at") or "")} · {a.get("reading_minutes") or 1} мин чтения · {_esc(a.get("category") or "Статьи")}'
        cards.append(
            f'                <a class="blog-card" href="{a["slug"]}/">\n'
            f'                    <div class="blog-meta">{meta}</div>\n'
            f'                    <h2>{_esc(a.get("title",""))}</h2>\n'
            f'                    <p class="blog-excerpt">{_esc(a.get("excerpt",""))}</p>\n'
            f'                    <span class="blog-read-more">Читать статью →</span>\n'
            f'                </a>'
        )
    return "\n\n".join(cards)


def build_index_itemlist(articles: list[dict]) -> str:
    items = [
        {"@type": "ListItem", "position": i + 1,
         "url": f"{SITE}/blog/{a['slug']}/", "name": a.get("title", "")}
        for i, a in enumerate(articles)
    ]
    payload = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "itemListElement": items,
    }
    return ('    <script type="application/ld+json">\n'
            + json.dumps(payload, ensure_ascii=False, indent=4)
            + "\n    </script>")


def build_sitemap_entries(articles: list[dict]) -> str:
    out = []
    for a in articles:
        lastmod = iso_date(a.get("updated_at") or a.get("published_at") or a.get("created_at") or "")
        out.append(
            f"  <url>\n"
            f"    <loc>{SITE}/blog/{a['slug']}/</loc>\n"
            f"    <lastmod>{lastmod}</lastmod>\n"
            f"    <changefreq>monthly</changefreq>\n"
            f"    <priority>0.7</priority>\n"
            f"  </url>"
        )
    return "\n".join(out)


def build_rss_items(articles: list[dict]) -> str:
    out = []
    for a in articles:
        out.append(
            f"    <item>\n"
            f"      <title>{_esc(a.get('title',''))}</title>\n"
            f"      <link>{SITE}/blog/{a['slug']}/</link>\n"
            f"      <guid isPermaLink=\"true\">{SITE}/blog/{a['slug']}/</guid>\n"
            f"      <pubDate>{rfc822(a.get('published_at') or a.get('created_at') or '')}</pubDate>\n"
            f"      <category>{_esc(a.get('category') or 'Статьи')}</category>\n"
            f"      <author>noreply@etoir.ru (эТОИР)</author>\n"
            f"      <description><![CDATA[{a.get('excerpt','')}]]></description>\n"
            f"    </item>"
        )
    return "\n\n".join(out)


# Marker constants
M = {
    "cards": ("<!-- BLOG:CARDS:START -->", "<!-- BLOG:CARDS:END -->"),
    "itemlist": ("<!-- BLOG:ITEMLIST:START -->", "<!-- BLOG:ITEMLIST:END -->"),
    "sitemap": ("<!-- BLOG:SITEMAP:START -->", "<!-- BLOG:SITEMAP:END -->"),
    "rss": ("<!-- BLOG:RSS:START -->", "<!-- BLOG:RSS:END -->"),
}


def _rewrite_file(path: str, regions: list[tuple[str, str, str]]) -> None:
    """Apply marker replacements to a file in place. Skips file if markers absent."""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    for start, end, payload in regions:
        try:
            text = replace_between(text, start, end, payload)
        except ValueError:
            return  # fail-safe: leave file untouched
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def regenerate_shared(landing_dir: str, published: list[dict]) -> None:
    """Regenerate blog index cards+itemlist, sitemap entries, rss items.

    ``published`` is the list of published articles, newest first.
    """
    _rewrite_file(
        os.path.join(landing_dir, "blog", "index.html"),
        [
            (*M["cards"], build_index_cards(published)),
            (*M["itemlist"], build_index_itemlist(published)),
        ],
    )
    _rewrite_file(
        os.path.join(landing_dir, "sitemap.xml"),
        [(*M["sitemap"], build_sitemap_entries(published))],
    )
    _rewrite_file(
        os.path.join(landing_dir, "rss.xml"),
        [(*M["rss"], build_rss_items(published))],
    )
