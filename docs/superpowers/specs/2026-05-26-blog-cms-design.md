# Блог-CMS для etoir.ru — дизайн

**Дата:** 2026-05-26
**Статус:** на согласовании
**Подход:** A — API рендерит статические файлы в bind-mounted `landing/`

## Проблема

Сейчас добавление статьи в `landing/blog/` — это ручная вёрстка HTML: полный `<head>`
с meta/OG/Twitter/тремя блоками JSON-LD, разметка тела статьи с нужными CSS-классами,
правка карточек в `blog/index.html`, добавление записей в `sitemap.xml` и `rss.xml`.
Каждая публикация требует деплоя. Нужен инструмент, чтобы писать статьи «на ходу»
в веб-редакторе, с автоматической SEO-обвязкой и публикацией без пересборки контейнеров.

## Решения, принятые при брейншторме

1. **Кто пишет:** автор пишет текст сам в веб-редакторе; система берёт на себя только SEO.
2. **Формат редактора:** классический Word-style (верхняя панель форматирования), не блочный.
3. **Возможности v1:** загрузка картинок, редактирование/удаление статей, черновики + превью,
   ручная правка SEO-полей.
4. **Архитектура:** Approach A — статические файлы, рендеримые API в bind-mount `landing/`.

## Цели / не-цели

**Цели (v1):**
- Создание, редактирование, удаление статей через защищённый веб-интерфейс.
- Word-style редактор тела статьи (заголовки, жирный/курсив, списки, ссылки, картинки, таблицы, цитаты).
- Структурные поля: hero-изображение, врезка «Коротко», список FAQ, категория, краткое описание.
- Кнопка вставки CTA-блока в тело.
- Черновики, превью без публикации, публикация одним действием без деплоя.
- Автоматическая SEO-обвязка, идентичная текущим статьям (см. ниже).
- Авто-обновление `blog/index.html`, `sitemap.xml`, `rss.xml` с сохранением ручного контента.
- 4 существующие статьи остаются как есть и не выпадают из индекса/карты сайта.

**Не-цели (v1):**
- Генерация текста ИИ (откладываем; возможна как отдельная фича позже).
- Редактирование тела 4 легаси-статей через редактор (правится как файл; в CMS — только метаданные карточки).
- Мультиавторство, роли, комментарии, версионирование/откат, расписание публикаций.
- Полнотекстовый поиск по блогу.

## Архитектура

```
nginx (без изменений в обслуживании статики)
  ├── /                         → landing/ (static, read-only mount)
  ├── /blog/<slug>/             → landing/blog/<slug>/index.html (создаётся API)
  ├── /api/                     → api:8000
  └── /admin/                   → api:8000  (вкл. /admin/blog/ — редактор)

api (FastAPI)
  ├── читает/пишет источник статей в SQLite (/data, том responses-data)
  └── рендерит и пишет статические файлы в /landing (bind-mount ./landing, rw)
```

Ключевая идея: `landing/` — это host bind-mount. API пишет туда реальные файлы,
nginx сразу их отдаёт. SQLite хранит **источник** (текст + поля) для повторного
редактирования; HTML-файл — это **отрендеренный вывод**.

### Изменения инфраструктуры

- **docker-compose.yml**: в сервис `api` добавить bind-mount `./landing:/landing` (rw)
  и переменную `LANDING_DIR=/landing`. (nginx-маунт `./landing:/app/landing:ro` не трогаем.)
- **nginx/etoir.conf**: в server-блок `etoir.ru` добавить `client_max_body_size 25M;`
  (нужно для загрузки изображений через `/admin/blog/`). Маршруты не меняются —
  `/admin/` уже проксируется в API.
- **api/requirements.txt**: добавить `Jinja2` (рендер шаблона), `Pillow` (оптимизация
  изображений), `bleach` (санитизация HTML из редактора).
- **TinyMCE**: GPL-сборка через jsDelivr CDN
  (`cdn.jsdelivr.net/npm/tinymce@7` + языковой пакет `tinymce-i18n`), `license_key: 'gpl'`.
  Без бандлера/сборки и без вендоринга файлов.

> Реализация (факт): Jinja2-шаблон статьи встроен строкой в `api/blog.py`
> (а не в отдельную папку `templates/`), чтобы рендер оставался чистой,
> тестируемой функцией без загрузки шаблонов с диска.

## Модель данных

Новая таблица SQLite `articles` (в том же `/data/responses.db`, создаётся в `db.init_db()`):

| Колонка | Тип | Назначение |
|---|---|---|
| `id` | INTEGER PK | |
| `slug` | TEXT UNIQUE | URL: `/blog/<slug>/` |
| `kind` | TEXT | `post` (рендерится CMS) или `legacy` (файл уже есть, только метаданные) |
| `status` | TEXT | `draft` или `published` |
| `title` | TEXT | H1 статьи |
| `seo_title` | TEXT | `<title>`; по умолчанию = `title`, перезаписывается вручную |
| `meta_description` | TEXT | meta description; по умолчанию = `excerpt` |
| `excerpt` | TEXT | текст карточки в индексе + описание в RSS |
| `category` | TEXT | `article:section`, метка категории на карточке |
| `keywords` | TEXT | meta keywords / JSON-LD keywords |
| `lead` | TEXT | вводный абзац (`.article-lead`) |
| `quick_answer` | TEXT | врезка «Коротко» (опционально) |
| `hero_image` | TEXT | путь к hero-изображению |
| `hero_alt` | TEXT | alt hero (SEO) |
| `hero_caption` | TEXT | подпись под hero (опционально) |
| `content_html` | TEXT | санитизированный HTML тела из редактора |
| `faq_json` | TEXT | JSON-массив `[{q,a}, …]` → FAQ-аккордеон + FAQPage |
| `read_also_json` | TEXT | опц. ручные ссылки «Читайте также»; иначе авто |
| `created_at` | TEXT | ISO-8601 |
| `published_at` | TEXT | ISO-8601 (дата первой публикации) |
| `updated_at` | TEXT | ISO-8601 (дата последнего изменения) |
| `reading_minutes` | INTEGER | вычисляется при рендере |
| `word_count` | INTEGER | вычисляется при рендере |

Легаси-статьи сидируются как строки `kind='legacy'` (slug, title, excerpt, category,
published_at, reading_minutes) — тело не хранится. Генерация индекса/sitemap/rss
итерирует все строки; для `legacy` ссылка ведёт на существующий файл, рендер тела не выполняется.

## SEO-автоматика (что генерируется автоматически)

Из полей статьи модуль `blog.py` строит **полную** обвязку, идентичную текущим статьям:

- **slug** — транслитерация title (ru→lat), нормализация, проверка уникальности; правится вручную.
- **`<title>`** = `seo_title`; **meta description** = `meta_description`; **canonical** = `https://etoir.ru/blog/<slug>/`.
- **Open Graph**: title, description, `type=article`, url, image (+alt/width/height), locale,
  site_name, `article:published_time`, `article:modified_time`, `article:author`, `article:section`, `article:tag`.
- **Twitter Card**: `summary_large_image` + title/description/image/alt.
- **preload** hero-изображения; **RSS alternate** `<link>`.
- **reading time** = `ceil(word_count / 180)` (≈180 слов/мин для русского); словосчёт по тексту тела.
- **JSON-LD Article** (headline, description, datePublished, dateModified, inLanguage,
  author/publisher Organization, image ImageObject, mainEntityOfPage, articleSection, keywords, wordCount, about).
- **JSON-LD BreadcrumbList** (Главная → Блог → заголовок).
- **JSON-LD FAQPage** — только если задан хотя бы один FAQ.
- **Table of contents** — строится существующим скриптом из H2 (серверу делать нечего, кроме `id`).
- **«Читайте также»** — последние 3 другие статьи (или ручной список из `read_also_json`).
- **Оптимизация изображений** при загрузке: ресайз до макс. ширины (≈1600px), конверсия в WebP,
  имя файла из slug + суффикс; alt запрашивается у автора (поле обязательно).
- **Карточка** в `blog/index.html`, запись в `sitemap.xml` и `rss.xml`.

Шаблон страницы — Jinja2-файл, повторяющий структуру `cmms-vs-excel/index.html`
(шапка/подвал, `.article-layout` с TOC, breadcrumb, hero `<figure>`, `.quick-answer`,
`.article-lead`, тело, inline-CTA, FAQ-блок, `.read-also`, мобильный sticky-CTA, TOC/CTA-скрипты,
аналитика Yandex.Metrika).

## Редактор (Word-style)

- **Библиотека:** TinyMCE (self-hosted, community/GPL). Панель: заголовки (H2/H3), bold/italic,
  списки (ul/ol), ссылки, изображения, таблицы, цитата, очистка форматирования, кнопка «Вставить CTA».
- **Структурные поля вне тела** (то, что flat-редактор делает плохо):
  - hero-изображение + alt + подпись;
  - врезка «Коротко» (textarea);
  - категория, краткое описание (excerpt), keywords;
  - FAQ — повторитель пар «вопрос / ответ»;
  - блок SEO (свернут): seo_title, meta_description, slug — авто-значения, правятся вручную.
- **CTA-блок:** кнопка панели вставляет в тело размеченный CTA (текст + ссылка на `/#contact`).
  Дополнительно система всегда добавляет финальный CTA перед «Читайте также».
- **Санитизация:** HTML из редактора чистится `bleach` (белый список тегов/атрибутов),
  затем элементам присваиваются нужные CSS-классы при рендере (таблицы, figure и т.д.).

## Безопасная регенерация общих файлов

`sitemap.xml`, `rss.xml`, `blog/index.html` содержат ручной контент (главная, privacy и пр.).
Один раз вставляем маркеры `<!-- BLOG:START -->` … `<!-- BLOG:END -->` вокруг блок-секций.
API заменяет **только** содержимое между маркерами; остальное сохраняется без изменений.
Если маркеры отсутствуют — операция логирует ошибку и не трогает файл (fail-safe).

## API-эндпоинты (все под `/admin/`, Basic-auth `_verify_admin`)

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/admin/blog/` | UI редактора (список + форма) |
| GET | `/admin/blog/api/articles` | список статей (JSON) |
| GET | `/admin/blog/api/articles/{id}` | одна статья (JSON) |
| POST | `/admin/blog/api/articles` | создать черновик |
| PUT | `/admin/blog/api/articles/{id}` | обновить |
| POST | `/admin/blog/api/articles/{id}/publish` | рендер + запись файлов + регенерация index/sitemap/rss |
| POST | `/admin/blog/api/articles/{id}/unpublish` | удалить файлы + регенерация |
| DELETE | `/admin/blog/api/articles/{id}` | удалить (и файлы, если опубликована) |
| POST | `/admin/blog/api/upload` | загрузка изображения → оптимизация → URL |
| GET | `/admin/blog/preview/{id}` | отрендерить HTML без записи на диск |

## Структура файлов

```
api/
  main.py        # + blog-роуты (импортируют функции из blog.py)
  blog.py        # NEW: slugify, reading_time, render_article, render_card,
                 #      regenerate_index/sitemap/rss (marker-replace), sanitize
  db.py          # + таблица articles, CRUD, seed легаси
  templates/     # NEW: Jinja2-шаблон статьи + индекс-карточки
  static/admin/  # NEW: HTML/JS редактора (или landing/admin-assets/)
landing/
  admin-assets/tinymce/   # NEW: self-hosted TinyMCE
  blog/<slug>/index.html  # генерируется
  blog/<slug>/img/*       # генерируется
docs/superpowers/specs/2026-05-26-blog-cms-design.md  # этот документ
```

## Тестирование

- **Юнит-тесты `blog.py`** (чистые функции): slugify (включая транслит и коллизии),
  reading_time, рендер статьи (наличие canonical/OG/JSON-LD/FAQPage), marker-replace
  (сохранение контента вне маркеров, fail-safe при отсутствии маркеров).
- **Эндпоинт-тесты** через FastAPI `TestClient` с временным `LANDING_DIR` (tmp_path):
  create→publish пишет ожидаемые файлы; unpublish/delete их убирает; upload отдаёт URL и
  сохраняет оптимизированный файл; Basic-auth обязателен.
- Примечание: активный код — в `api/`; тесты блога импортируют из `api/` (в отличие от
  существующих тестов, нацеленных на корневой `main.py`).

## Риски и заметки

- **Размер изображений / время рендера** — Pillow ресайз ограничивает; крупные загрузки
  лимитируются `client_max_body_size`.
- **Конкуренция записи** — публикации редки и однопользовательские; регенерация индекса —
  быстрая операция; явная блокировка не нужна в v1.
- **Целостность маркеров** — fail-safe (не трогать файл без маркеров) защищает sitemap/rss.
- **Git working tree** — сгенерированные статьи появятся в репозитории (это плюс: бэкап/история);
  при необходимости договоримся о соглашении по коммитам.
- **Восстановление на чистом сервере** — источник в SQLite; команда «перегенерировать всё»
  (можно добавить как admin-эндпоинт позже) воссоздаёт файлы из БД.
