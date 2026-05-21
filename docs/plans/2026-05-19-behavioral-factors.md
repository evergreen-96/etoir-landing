# Поведенческие факторы (Tasks 16–17) + порт фазы 1 в прод — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Удлинить session duration и снизить bounce rate прод-лендинга `D:\prod_projects\etoir-landing\landing\` через ROI-калькулятор, слайдшоу, аккордеон методологии и блог с sticky-навигацией; параллельно перенести недостающую часть фазы 1 SEO (расширенный FAQ, отрасли, сравнение, блог) из `S:\_python_rojects\e-toir-langing\`.

**Architecture:** Single-file inline HTML/CSS/JS (без сборки, без библиотек), всё дописывается в `landing/index.html` и в новые HTML-файлы блога. JS-логика повторно используемая: `initSlideshow()`, `initToc()`, `initStickyCta()` дублируется между файлами (3 статьи) — допустимая копипаста, вынос в общий файл не делаем по соглашению проекта.

**Tech Stack:** HTML5, vanilla JS (ES2017+), CSS Grid/Flexbox, JSON-LD (schema.org), Inter/JetBrains Mono шрифты, Я.Метрика 107942912, GA4 G-DS3D1SLNHD.

**Spec:** `docs/superpowers/specs/2026-05-19-behavioral-factors-design.md`

**Source-of-truth для контента:** S-репо `S:\_python_rojects\e-toir-langing\` — оттуда копируются тексты FAQ, статей, отраслей и адаптируются под бренд «эТОИР» (без дефиса).

**Все пути ниже** — относительно прод-репо `D:\prod_projects\etoir-landing\`.

---

## Замечания о тестировании

Проект статичный, юнит-тестов для HTML нет. «Тест» каждой задачи = ручная smoke-проверка в браузере. Запускать локальный сервер для всех проверок:

```bash
cd D:\prod_projects\etoir-landing\landing
python -m http.server 8000
```

Открывать `http://localhost:8000/`. Для проверки мобильной вёрстки использовать DevTools → Device Mode (iPhone SE 375×667, iPhone 12 Pro 390×844).

Для JSON-LD валидировать через [Rich Results Test](https://search.google.com/test/rich-results) — копировать содержимое страницы и вставлять как «Code», либо после деплоя проверять по URL.

---

# Часть A. Порт фазы 1 SEO в прод

## Task 1: Расширить FAQ с 6 до 13 вопросов (и синхронизировать JSON-LD)

**Files:**
- Modify: `landing/index.html` (секция FAQ ~стр. 4107, JSON-LD `FAQPage` ~стр. 109)
- Reference: `S:\_python_rojects\e-toir-langing\index.html` (искать `class="faq-item"` и `"@type": "FAQPage"`)

- [ ] **Step 1: Изучить структуру существующего FAQ в проде**

Открыть `landing/index.html`, найти секцию `<h2 class="section-title">Частые вопросы</h2>` (~стр. 4107). Запомнить разметку каждого `.faq-item` (классы, ARIA-атрибуты, кнопка-аккордеон).

- [ ] **Step 2: Извлечь 7 новых вопросов из S-репо**

Из `S:\_python_rojects\e-toir-langing\index.html` (секция `<section id="faq">`) выбрать вопросы, которых нет в проде. Минимум 7 штук:

1. Чем эТОИР отличается от 1С:ТОИР?
2. Подходит ли эТОИР для малого производства (до 50 единиц оборудования)?
3. Что такое MTBF и MTTR — и считает ли их эТОИР?
4. Как происходит интеграция с 1С:УПП / 1С:ERP?
5. Поддерживается ли SCADA / OPC UA?
6. Эта система в Реестре Минцифры?
7. Что такое наряд-заказ в эТОИР?

В ответах: везде заменить «e-TOIR» → «эТОИР», адаптировать названия секций под прод (если ссылки `#features` называются иначе в проде — поправить).

- [ ] **Step 3: Дописать 7 новых `.faq-item` в HTML-секцию FAQ**

Скопировать разметку существующего `.faq-item` 7 раз, в каждой заменить вопрос и ответ. Сохранить порядок: новые вопросы добавлять после существующих, чтобы продовые остались сверху.

- [ ] **Step 4: Обновить JSON-LD `FAQPage`**

Найти блок `"@type": "FAQPage"` (~стр. 109). Дописать 7 элементов в массив `"mainEntity"`. Структура каждого:

```json
{
  "@type": "Question",
  "name": "Чем эТОИР отличается от 1С:ТОИР?",
  "acceptedAnswer": {
    "@type": "Answer",
    "text": "1С:ТОИР — модуль внутри 1С, требующий конфигурации и поддержки 1С-программистов. эТОИР — самостоятельный продукт с веб-интерфейсом и мобильным приложением для слесарей, готов к работе за день."
  }
}
```

**Важно:** текст в JSON-LD должен буква-в-букву совпадать с текстом в HTML.

- [ ] **Step 5: Smoke-проверка в браузере**

Запустить локальный сервер, открыть главную, проскроллить до FAQ. Проверить:
- 13 вопросов отображаются
- Каждый раскрывается по клику
- Раскрытие работает с клавиатуры (Tab + Enter/Space)

Прогнать через Rich Results Test — должно быть распознано 13 Question/Answer пар.

- [ ] **Step 6: Commit**

```bash
git add landing/index.html
git commit -m "feat(seo): extend FAQ from 6 to 13 questions with JSON-LD sync"
```

---

## Task 2: Добавить секцию «Для каких отраслей подходит эТОИР»

**Files:**
- Modify: `landing/index.html` (вставить после секции «Преимущества», перед секцией «Интеграции»)
- Reference: `S:\_python_rojects\e-toir-langing\index.html` (искать `id="industries"`)

- [ ] **Step 1: Найти подходящее место для вставки**

В `landing/index.html` найти `<h2 class="section-title">Почему выбирают эТОИР</h2>` (~стр. 3838). После закрывающего `</section>` этого блока — вставить новую секцию `<section id="industries">`. Перед `<h2>Подключается к вашим системам</h2>` (~стр. 3883).

- [ ] **Step 2: Скопировать структуру из S и адаптировать**

Скопировать секцию `id="industries"` из S-репо. Внутри:
- `<h2 class="section-title">Для каких отраслей подходит эТОИР</h2>`
- Сетка из 6 карточек: машиностроение, пищевое производство, металлургия, химия, энергетика, добыча/ГОК.
- Каждая карточка: иконка (SVG inline или Emoji), `<h3>` с отраслью, 30–50 слов про специфику ТОиР именно в этой отрасли (с релевантными ключами).

Везде «e-TOIR» → «эТОИР».

- [ ] **Step 3: Подогнать CSS-классы под прод**

Прод использует свои названия (`.section-title`, `.fw-h2`). Если в S карточки имеют класс `.industry-card`, оставить его — добавить минимальный inline-CSS в существующий `<style>` блок прода:

```css
.industries-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin-top: 40px;
}
.industry-card {
  background: var(--bg-card, #fff);
  border: 1px solid var(--border, #e2e8f0);
  border-radius: 16px;
  padding: 32px;
  transition: transform 0.2s, box-shadow 0.2s;
}
.industry-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.08);
}
.industry-card .industry-icon {
  font-size: 40px;
  margin-bottom: 16px;
}
.industry-card h3 {
  font-size: 1.25rem;
  margin: 0 0 12px;
  color: var(--text-primary, #1e293b);
}
.industry-card p {
  color: var(--text-secondary, #475569);
  line-height: 1.6;
  margin: 0;
}
@media (max-width: 768px) {
  .industries-grid { grid-template-columns: 1fr; gap: 16px; }
  .industry-card { padding: 24px; }
}
```

Если переменные `--bg-card`, `--border` в проде называются иначе — подменить (грепнуть в `:root`).

- [ ] **Step 4: Smoke-проверка**

Открыть в браузере, проскроллить до секции. Проверить на desktop (1440px), tablet (768px), mobile (375px) — карточки корректно перестраиваются.

- [ ] **Step 5: Commit**

```bash
git add landing/index.html
git commit -m "feat(seo): add industries section with 6 cards"
```

---

## Task 3: Добавить таблицу сравнения «эТОИР vs Excel vs 1С:ТОИР»

**Files:**
- Modify: `landing/index.html` (вставить после секции «Реальные цифры», ~стр. 3211)
- Reference: `S:\_python_rojects\e-toir-langing\index.html` (искать `id="comparison"`)

- [ ] **Step 1: Скопировать структуру таблицы из S**

В S-репо найти `<section id="comparison">`. Структура: 8 строк × 3 столбца. Функции для сравнения:

1. Учёт оборудования
2. Планирование ТО
3. Мобильное приложение для слесарей
4. Аналитика MTBF/MTTR
5. Интеграция с 1С / ERP
6. Стоимость владения
7. Скорость внедрения
8. Поддержка из Реестра Минцифры

Каждая ячейка для Excel/1С:ТОИР — короткая фраза или «—»; для эТОИР — «✓» с подписью.

- [ ] **Step 2: Вставить секцию в прод**

В `landing/index.html` после `<h2 class="rs-title">Реальные цифры наших клиентов</h2>` и закрывающего `</section>` — вставить новый блок:

```html
<section id="comparison" class="comparison-section">
  <div class="container">
    <h2 class="section-title">Чем эТОИР лучше Excel и 1С:ТОИР</h2>
    <p class="section-subtitle">Сравнение по 8 ключевым параметрам</p>
    <div class="comparison-table-wrapper">
      <table class="comparison-table">
        <thead>
          <tr>
            <th>Функция</th>
            <th class="col-excel">Excel</th>
            <th class="col-1c">1С:ТОИР</th>
            <th class="col-etoir">эТОИР</th>
          </tr>
        </thead>
        <tbody>
          <!-- 8 строк -->
        </tbody>
      </table>
    </div>
  </div>
</section>
```

Заполнить 8 `<tr>` контентом из S-репо.

- [ ] **Step 3: Добавить CSS для таблицы**

```css
.comparison-table-wrapper { overflow-x: auto; margin-top: 32px; }
.comparison-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 720px;
}
.comparison-table th,
.comparison-table td {
  padding: 16px 20px;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
}
.comparison-table thead th {
  background: #f8fafc;
  font-weight: 600;
  color: #1e293b;
}
.comparison-table .col-etoir { background: rgba(37, 99, 235, 0.04); }
.comparison-table tbody tr:hover { background: #fafafa; }
@media (max-width: 768px) {
  .comparison-table { font-size: 0.9rem; min-width: 600px; }
  .comparison-table th, .comparison-table td { padding: 12px 14px; }
}
```

- [ ] **Step 4: Smoke-проверка**

Открыть в браузере на desktop и mobile. На мобильных таблица скроллится горизонтально (`overflow-x: auto`). Текст читается.

- [ ] **Step 5: Commit**

```bash
git add landing/index.html
git commit -m "feat(seo): add comparison table eTOIR vs Excel vs 1C:TOIR"
```

---

## Task 4: BreadcrumbList JSON-LD на главной

**Files:**
- Modify: `landing/index.html` (добавить в `<head>` рядом с другими JSON-LD ~стр. 49)

- [ ] **Step 1: Добавить JSON-LD блок**

В `<head>` после существующих `<script type="application/ld+json">` — добавить:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Главная",
      "item": "https://e-toir.ru/"
    }
  ]
}
</script>
```

- [ ] **Step 2: Валидация**

Скопировать содержимое страницы в Rich Results Test, проверить что BreadcrumbList распознан без ошибок.

- [ ] **Step 3: Commit**

```bash
git add landing/index.html
git commit -m "feat(seo): add BreadcrumbList JSON-LD to main page"
```

---

## Task 5: Создать индекс блога

**Files:**
- Create: `landing/blog/index.html`
- Reference: `S:\_python_rojects\e-toir-langing\blog\index.html`

- [ ] **Step 1: Создать каталог и файл**

```bash
mkdir landing\blog
```

- [ ] **Step 2: Создать `landing/blog/index.html`**

Скопировать из S `blog/index.html`. Изменения:
- Бренд «e-TOIR» → «эТОИР» везде (в `<title>`, `<meta>`, `<h1>`, текстах карточек, в JSON-LD).
- Канонический URL: `https://e-toir.ru/blog/`
- OG-image: использовать `../images/og-image.png` (относительно blog/) — у прода свой OG.
- Шапка и футер — скопировать из `landing/index.html` (логотип, навигация, контакты), не из S. Внутренние ссылки навигации должны вести на `../` (главная) и `../#features`, `../#contact` и т.д.
- В шапке добавить ссылку «Блог» с активным состоянием.

Содержимое body:
- `<h1>Блог о ТОиР</h1>`
- `<p class="lead">Практические статьи о внедрении CMMS, расчёте эффективности и автоматизации ремонтов.</p>`
- Сетка из 3 карточек статей:
  1. «эТОИР vs Excel: почему таблицы больше не работают» → `cmms-vs-excel/`
  2. «Как внедрить ТОиР-систему: 7 шагов» → `kak-vnedrit-toir-sistemu/`
  3. «Зачем автоматизировать ТОиР: 6 причин» → `zachem-avtomatizirovat-toir/`

- JSON-LD `BreadcrumbList`: Главная → Блог.
- JSON-LD `ItemList` со списком статей.

- [ ] **Step 3: Стилизация карточек статей**

CSS — в inline `<style>` файла:

```css
.blog-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 24px;
  margin-top: 48px;
}
.blog-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 28px;
  transition: transform 0.2s, box-shadow 0.2s;
  text-decoration: none;
  color: inherit;
  display: flex;
  flex-direction: column;
}
.blog-card:hover { transform: translateY(-4px); box-shadow: 0 12px 32px rgba(0,0,0,0.08); }
.blog-card .blog-meta { color: #64748b; font-size: 0.875rem; margin-bottom: 12px; }
.blog-card h2 { font-size: 1.375rem; margin: 0 0 12px; color: #1e293b; }
.blog-card .blog-excerpt { color: #475569; line-height: 1.6; margin: 0 0 16px; flex: 1; }
.blog-card .blog-read-more { color: #2563eb; font-weight: 600; }
```

- [ ] **Step 4: Smoke-проверка**

Открыть `http://localhost:8000/blog/` → 3 карточки, навигация в шапке ведёт на `/`, кликабельные карточки ведут на (пока несуществующие) URL. Rich Results Test: BreadcrumbList + ItemList без ошибок.

- [ ] **Step 5: Commit**

```bash
git add landing/blog/index.html
git commit -m "feat(blog): create blog index page with 3 article cards"
```

---

## Task 6: Создать статью `cmms-vs-excel`

**Files:**
- Create: `landing/blog/cmms-vs-excel/index.html`
- Reference: `S:\_python_rojects\e-toir-langing\blog\cmms-vs-excel\index.html`

- [ ] **Step 1: Создать каталог и файл**

```bash
mkdir landing\blog\cmms-vs-excel
```

- [ ] **Step 2: Скопировать статью из S и адаптировать**

Структура файла:

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>эТОИР vs Excel: почему таблицы больше не работают для управления ТОиР</title>
  <meta name="description" content="...">
  <link rel="canonical" href="https://e-toir.ru/blog/cmms-vs-excel/">
  <!-- OG, Twitter, fonts (как в landing/index.html) -->
  <!-- GA4 + Я.Метрика (как в landing/index.html — копировать целиком) -->
  <!-- JSON-LD: Article + BreadcrumbList -->
  <style>/* стили статьи + sticky CTA + TOC — см. шаги 4–6 */</style>
</head>
<body>
  <!-- Шапка (как в landing/index.html, скопировать) -->
  <main class="article-layout">
    <aside class="article-toc" aria-label="Содержание статьи">
      <div class="article-toc-title">Содержание</div>
      <ul class="article-toc-list"><!-- JS заполнит --></ul>
    </aside>
    <article class="article-content">
      <nav class="breadcrumb">
        <a href="/">Главная</a> →
        <a href="/blog/">Блог</a> →
        <span>эТОИР vs Excel</span>
      </nav>
      <h1>эТОИР vs Excel: почему таблицы больше не работают для управления ТОиР</h1>
      <p class="article-meta">19 мая 2026 · 7 мин чтения</p>
      <p class="article-lead">Первый абзац — превью статьи (~80 слов).</p>
      <!-- TOC-mobile вставляется сразу здесь, см. шаг 5 -->
      <details class="article-toc-mobile">
        <summary>📋 Содержание статьи</summary>
        <ul><!-- JS заполнит --></ul>
      </details>
      <h2 id="h2-1">Раздел 1</h2>
      <!-- основной текст, ~900 слов, разбит на 5–6 H2 -->
    </article>
  </main>
  <!-- Sticky mobile CTA, см. шаг 6 -->
  <!-- Футер (скопировать из landing/index.html) -->
  <script>/* initToc + initStickyCta — см. шаги 4 и 6 */</script>
</body>
</html>
```

**Контент:** скопировать тело статьи из S-репо целиком. Заменить «e-TOIR» → «эТОИР».

**Контекстные ссылки внутри тела** (минимум 3 + 2):
- 3 ссылки на главную: одна на `/#features`, одна на `/#industries`, одна на `/#comparison`.
- 2 ссылки на другие статьи: `../kak-vnedrit-toir-sistemu/`, `../zachem-avtomatizirovat-toir/`.

Стиль ссылок: `<a href="/#comparison">таблица сравнения</a>` — стандартный underline.

- [ ] **Step 3: JSON-LD блоки**

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "эТОИР vs Excel: почему таблицы больше не работают для управления ТОиР",
  "datePublished": "2026-05-19",
  "dateModified": "2026-05-19",
  "author": { "@type": "Organization", "name": "эТОИР" },
  "publisher": {
    "@type": "Organization",
    "name": "эТОИР",
    "logo": { "@type": "ImageObject", "url": "https://e-toir.ru/landing/images/logo.png" }
  },
  "image": "https://e-toir.ru/landing/images/og-image.png",
  "mainEntityOfPage": "https://e-toir.ru/blog/cmms-vs-excel/"
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "Главная", "item": "https://e-toir.ru/" },
    { "@type": "ListItem", "position": 2, "name": "Блог", "item": "https://e-toir.ru/blog/" },
    { "@type": "ListItem", "position": 3, "name": "эТОИР vs Excel" }
  ]
}
</script>
```

- [ ] **Step 4: CSS для article-layout + TOC**

```css
.article-layout {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 24px;
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 48px;
}
.article-toc {
  position: sticky;
  top: 100px;
  align-self: start;
  max-height: calc(100vh - 120px);
  overflow-y: auto;
  font-size: 0.9rem;
}
.article-toc-title { font-weight: 700; margin-bottom: 12px; color: #1e293b; }
.article-toc-list { list-style: none; padding: 0; margin: 0; border-left: 2px solid #e2e8f0; }
.article-toc-list li { padding: 6px 0 6px 16px; }
.article-toc-list a {
  color: #64748b;
  text-decoration: none;
  display: block;
  transition: color 0.2s;
}
.article-toc-list a:hover { color: #2563eb; }
.article-toc-list li.active {
  border-left: 2px solid #2563eb;
  margin-left: -2px;
}
.article-toc-list li.active a { color: #2563eb; font-weight: 600; }
.article-toc-mobile { display: none; margin: 24px 0; padding: 16px; background: #f8fafc; border-radius: 12px; }
.article-toc-mobile summary { cursor: pointer; font-weight: 600; color: #1e293b; }
.article-toc-mobile ul { list-style: none; padding: 12px 0 0; margin: 0; }
.article-toc-mobile li { padding: 6px 0; }
.article-toc-mobile a { color: #2563eb; text-decoration: none; }
.article-content h2 { margin-top: 48px; scroll-margin-top: 100px; }
.article-content p, .article-content li { line-height: 1.7; }

@media (max-width: 1024px) {
  .article-layout { grid-template-columns: 1fr; gap: 24px; }
  .article-toc { display: none; }
  .article-toc-mobile { display: block; }
}
```

- [ ] **Step 5: JS — initToc()**

В `<script>` в конце `<body>`:

```js
function initToc() {
  const article = document.querySelector('.article-content');
  if (!article) return;
  const headings = article.querySelectorAll('h2');
  if (!headings.length) return;

  const desktopList = document.querySelector('.article-toc-list');
  const mobileList = document.querySelector('.article-toc-mobile ul');
  const mobileSummary = document.querySelector('.article-toc-mobile summary');

  headings.forEach((h, i) => {
    if (!h.id) h.id = 'h2-' + (i + 1);
    const text = h.textContent.trim();
    const link = `<li data-target="${h.id}"><a href="#${h.id}">${text}</a></li>`;
    if (desktopList) desktopList.insertAdjacentHTML('beforeend', link);
    if (mobileList) mobileList.insertAdjacentHTML('beforeend', link);
  });

  if (mobileSummary) {
    mobileSummary.textContent = `📋 Содержание (${headings.length} ${headings.length === 1 ? 'раздел' : 'разделов'})`;
  }

  // scroll-spy
  const tocItems = document.querySelectorAll('.article-toc-list li');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.id;
        tocItems.forEach(li => li.classList.toggle('active', li.dataset.target === id));
      }
    });
  }, { rootMargin: '-80px 0px -70% 0px', threshold: 0 });

  headings.forEach(h => observer.observe(h));
}

document.addEventListener('DOMContentLoaded', initToc);
```

- [ ] **Step 6: CSS + JS для sticky mobile CTA**

В `<style>`:

```css
.sticky-cta-mobile {
  display: none;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 56px;
  background: #2563eb;
  color: #fff;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  z-index: 100;
  transform: translateY(100%);
  transition: transform 0.3s ease;
  box-shadow: 0 -4px 12px rgba(0,0,0,0.12);
}
.sticky-cta-mobile.visible { transform: translateY(0); }
.sticky-cta-text { font-size: 0.875rem; font-weight: 500; flex: 1; padding-right: 12px; }
.sticky-cta-btn {
  background: #f59e0b;
  color: #1e293b;
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 600;
  text-decoration: none;
  font-size: 0.875rem;
  white-space: nowrap;
}
.sticky-cta-close {
  background: none;
  border: none;
  color: rgba(255,255,255,0.7);
  font-size: 18px;
  padding: 0 8px;
  cursor: pointer;
}
@media (max-width: 768px) {
  .sticky-cta-mobile { display: flex; }
}
```

В `<body>` перед футером:

```html
<div class="sticky-cta-mobile" aria-hidden="true">
  <span class="sticky-cta-text">Бесплатное демо за 30 минут</span>
  <a href="/#contact" class="sticky-cta-btn">Получить демо</a>
  <button class="sticky-cta-close" aria-label="Закрыть">✕</button>
</div>
```

В `<script>`:

```js
function initStickyCta() {
  const cta = document.querySelector('.sticky-cta-mobile');
  if (!cta) return;
  if (sessionStorage.getItem('sticky-cta-dismissed')) return;

  const article = document.querySelector('.article-content');
  if (!article) return;

  // Показать после скролла 40% статьи
  const showAfter = article.offsetTop + article.offsetHeight * 0.4;

  let shown = false;
  window.addEventListener('scroll', () => {
    if (shown) return;
    if (window.scrollY + window.innerHeight >= showAfter) {
      cta.classList.add('visible');
      cta.setAttribute('aria-hidden', 'false');
      shown = true;
    }
  }, { passive: true });

  cta.querySelector('.sticky-cta-close').addEventListener('click', () => {
    cta.classList.remove('visible');
    cta.setAttribute('aria-hidden', 'true');
    sessionStorage.setItem('sticky-cta-dismissed', '1');
  });

  cta.querySelector('.sticky-cta-btn').addEventListener('click', () => {
    if (window.ym) ym(107942912, 'reachGoal', 'sticky_cta_click');
    if (window.gtag) gtag('event', 'sticky_cta_click');
  });
}

document.addEventListener('DOMContentLoaded', initStickyCta);
```

- [ ] **Step 7: Smoke-проверка**

Открыть `http://localhost:8000/blog/cmms-vs-excel/`:
- Desktop: TOC слева, scroll-spy подсвечивает текущий H2 при прокрутке.
- Mobile (DevTools): TOC свёрнут в `<details>`, sticky CTA появляется при скролле >40%, закрывается крестиком и не возвращается до перезагрузки.
- Все внутренние ссылки кликабельны и ведут в нужные места.

JSON-LD Article + BreadcrumbList в Rich Results Test — без ошибок.

- [ ] **Step 8: Commit**

```bash
git add landing/blog/cmms-vs-excel/index.html
git commit -m "feat(blog): add cmms-vs-excel article with sticky TOC and mobile CTA"
```

---

## Task 7: Создать статью `kak-vnedrit-toir-sistemu`

**Files:**
- Create: `landing/blog/kak-vnedrit-toir-sistemu/index.html`
- Reference: `S:\_python_rojects\e-toir-langing\blog\kak-vnedrit-toir-sistemu\index.html`

- [ ] **Step 1: Создать каталог**

```bash
mkdir landing\blog\kak-vnedrit-toir-sistemu
```

- [ ] **Step 2: Создать файл по шаблону Task 6**

Точная копия структуры из Task 6 (head, JSON-LD, article-layout, TOC, sticky CTA, скрипты).

Изменения:
- `<title>`: «Как внедрить ТОиР-систему: пошаговый план за 7 шагов»
- `<meta description>`
- Canonical: `https://e-toir.ru/blog/kak-vnedrit-toir-sistemu/`
- В JSON-LD Article: `headline`, `mainEntityOfPage`
- В BreadcrumbList: «Как внедрить ТОиР-систему»
- В крошках: «Как внедрить ТОиР-систему»
- `<h1>`: «Как внедрить ТОиР-систему: пошаговый план за 7 шагов»
- Тело статьи: скопировать из S, заменить бренд, ~1000 слов, 7 H2-разделов (по числу шагов).

Контекстные ссылки (3 + 2):
- `/#features`, `/#advantages`, `/#contact`
- `../cmms-vs-excel/`, `../zachem-avtomatizirovat-toir/`

- [ ] **Step 3: Smoke-проверка**

Аналогично Task 6 шаг 7. Особо проверить: TOC показывает 7 пунктов.

- [ ] **Step 4: Commit**

```bash
git add landing/blog/kak-vnedrit-toir-sistemu/index.html
git commit -m "feat(blog): add kak-vnedrit-toir-sistemu article"
```

---

## Task 8: Создать статью `zachem-avtomatizirovat-toir`

**Files:**
- Create: `landing/blog/zachem-avtomatizirovat-toir/index.html`
- Reference: `S:\_python_rojects\e-toir-langing\blog\zachem-avtomatizirovat-toir\index.html`

- [ ] **Step 1: Создать каталог**

```bash
mkdir landing\blog\zachem-avtomatizirovat-toir
```

- [ ] **Step 2: Создать файл по шаблону Task 6**

Изменения:
- `<title>`: «Зачем автоматизировать ТОиР: 6 причин перейти на эТОИР»
- Canonical: `https://e-toir.ru/blog/zachem-avtomatizirovat-toir/`
- `<h1>` и BreadcrumbList — «Зачем автоматизировать ТОиР»
- Тело: ~650 слов, 6 H2 (по числу причин).

Контекстные ссылки (3 + 2):
- `/#industries`, `/#comparison`, `/#faq`
- `../cmms-vs-excel/`, `../kak-vnedrit-toir-sistemu/`

- [ ] **Step 3: Smoke-проверка**

Аналогично Task 6 шаг 7. TOC показывает 6 пунктов.

- [ ] **Step 4: Commit**

```bash
git add landing/blog/zachem-avtomatizirovat-toir/index.html
git commit -m "feat(blog): add zachem-avtomatizirovat-toir article"
```

---

## Task 9: Обновить sitemap.xml

**Files:**
- Modify: `landing/sitemap.xml`

- [ ] **Step 1: Перезаписать содержимое**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://e-toir.ru/</loc>
    <lastmod>2026-05-19</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://e-toir.ru/blog/</loc>
    <lastmod>2026-05-19</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://e-toir.ru/blog/cmms-vs-excel/</loc>
    <lastmod>2026-05-19</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://e-toir.ru/blog/kak-vnedrit-toir-sistemu/</loc>
    <lastmod>2026-05-19</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://e-toir.ru/blog/zachem-avtomatizirovat-toir/</loc>
    <lastmod>2026-05-19</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
</urlset>
```

- [ ] **Step 2: Smoke-проверка**

`curl http://localhost:8000/sitemap.xml` → 5 URL без ошибок XML.

- [ ] **Step 3: Commit**

```bash
git add landing/sitemap.xml
git commit -m "feat(seo): update sitemap with blog URLs"
```

---

## Task 10: Добавить ссылку на блог в шапку и футер главной

**Files:**
- Modify: `landing/index.html`

- [ ] **Step 1: Добавить ссылку в навигацию шапки**

Найти `<nav>` в `<header>` лендинга. Добавить пункт «Блог» перед пунктом контактов:

```html
<a href="/blog/" class="nav-link">Блог</a>
```

Стилизация — наследует существующий класс `.nav-link`.

- [ ] **Step 2: Добавить ссылку в футер**

Найти `<footer>`. В колонке навигации или рядом — добавить:

```html
<a href="/blog/">Блог</a>
```

- [ ] **Step 3: Smoke-проверка**

Открыть `/`, кликнуть «Блог» в шапке → попадает на `/blog/`. Аналогично из футера.

- [ ] **Step 4: Commit**

```bash
git add landing/index.html
git commit -m "feat(blog): add blog link to header and footer"
```

---

# Часть B. Поведенческие факторы (Tasks 16–17)

## Task 11: ROI-калькулятор

**Files:**
- Modify: `landing/index.html` (вставить между секцией «Реальные цифры» и таблицей сравнения — после Task 3)

- [ ] **Step 1: Вставить HTML-разметку секции**

В `landing/index.html` после `<section id="comparison">` (созданной в Task 3) или перед, в зависимости от композиции — вставить:

```html
<section id="roi-calculator" class="roi-section">
  <div class="container">
    <h2 class="section-title">Посчитайте, сколько эТОИР сэкономит вашему заводу</h2>
    <p class="section-subtitle">Калькулятор на основе средних показателей внедрений в РФ</p>

    <div class="roi-grid">
      <div class="roi-inputs">
        <label class="roi-field">
          <span class="roi-label">Часов простоев в месяц по парку</span>
          <input type="range" id="roi-hours" min="0" max="500" value="40" step="5">
          <output class="roi-output" data-for="roi-hours">40 ч</output>
        </label>

        <label class="roi-field">
          <span class="roi-label">Средняя стоимость часа простоя, ₽</span>
          <input type="range" id="roi-cost" min="5000" max="500000" value="50000" step="5000">
          <output class="roi-output" data-for="roi-cost">50 000 ₽</output>
        </label>

        <label class="roi-field">
          <span class="roi-label">Единиц критичного оборудования</span>
          <input type="range" id="roi-units" min="1" max="500" value="30" step="1">
          <output class="roi-output" data-for="roi-units">30 шт</output>
        </label>
      </div>

      <div class="roi-result">
        <div class="roi-result-label">Годовая экономия</div>
        <div class="roi-result-total" id="roi-total">— ₽</div>
        <ul class="roi-breakdown">
          <li>− <span id="roi-downtime">—</span> ₽ на простоях</li>
          <li>− <span id="roi-spares">—</span> ₽ на запчастях</li>
          <li>− <span id="roi-labor">—</span> ₽ на трудозатратах</li>
        </ul>
        <div class="roi-payback">Окупаемость эТОИР: <strong id="roi-payback">—</strong> месяцев</div>
        <a href="#contact" class="btn btn-primary roi-cta">Узнать точные цифры для вашего завода</a>
        <button type="button" class="roi-methodology-link" aria-controls="roi-methodology">Откуда эти цифры?</button>
      </div>
    </div>
  </div>
</section>
```

- [ ] **Step 2: Добавить CSS**

В `<style>` блок:

```css
.roi-section { background: linear-gradient(135deg, #f8fafc 0%, #eff6ff 100%); padding: 80px 0; }
.roi-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 48px;
  margin-top: 48px;
  align-items: start;
}
.roi-field { display: block; margin-bottom: 28px; }
.roi-label { display: block; font-weight: 500; color: #1e293b; margin-bottom: 8px; }
.roi-field input[type="range"] {
  width: 100%;
  height: 6px;
  background: #cbd5e1;
  border-radius: 3px;
  outline: none;
  -webkit-appearance: none;
}
.roi-field input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  background: #2563eb;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(37, 99, 235, 0.4);
}
.roi-output { display: inline-block; margin-top: 8px; font-weight: 600; color: #2563eb; }
.roi-result {
  background: #fff;
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.06);
  border: 1px solid #e2e8f0;
}
.roi-result-label { font-size: 0.875rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px; }
.roi-result-total {
  font-size: 2.75rem;
  font-weight: 700;
  color: #2563eb;
  margin-bottom: 24px;
  line-height: 1.1;
  font-feature-settings: "tnum";
}
.roi-breakdown { list-style: none; padding: 0; margin: 0 0 24px; }
.roi-breakdown li { padding: 6px 0; color: #475569; }
.roi-payback { padding: 16px; background: #f0fdf4; border-radius: 12px; color: #166534; margin-bottom: 24px; }
.roi-payback strong { color: #15803d; }
.roi-cta { display: inline-block; margin-bottom: 16px; }
.roi-methodology-link {
  background: none;
  border: none;
  color: #2563eb;
  cursor: pointer;
  text-decoration: underline;
  font-size: 0.875rem;
}
@media (max-width: 768px) {
  .roi-grid { grid-template-columns: 1fr; gap: 32px; }
  .roi-result { padding: 28px; }
  .roi-result-total { font-size: 2rem; }
}
```

- [ ] **Step 3: Добавить JS-логику**

В блок `<script>` в конце `<body>`:

```js
const ROI_CONFIG = {
  downtimeReductionPct: 0.38,
  sparesAvgCostPerUnit: 80000,
  sparesReductionPct: 0.05,
  laborHourlyRate: 1500,
  laborWasteRatio: 0.25,
  etoirAnnualCost: 1080000
};

function formatRub(n) {
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 }).format(n);
}

function calculateRoi() {
  const hours = parseInt(document.getElementById('roi-hours').value, 10);
  const cost = parseInt(document.getElementById('roi-cost').value, 10);
  const units = parseInt(document.getElementById('roi-units').value, 10);

  const downtime = hours * 12 * cost * ROI_CONFIG.downtimeReductionPct;
  const spares = units * ROI_CONFIG.sparesAvgCostPerUnit * ROI_CONFIG.sparesReductionPct;
  const labor = hours * 12 * ROI_CONFIG.laborHourlyRate * ROI_CONFIG.laborWasteRatio;
  const total = downtime + spares + labor;
  const payback = total > 0 ? Math.max(1, Math.round((ROI_CONFIG.etoirAnnualCost / total) * 12)) : '∞';

  document.getElementById('roi-total').textContent = formatRub(total) + ' ₽';
  document.getElementById('roi-downtime').textContent = formatRub(downtime);
  document.getElementById('roi-spares').textContent = formatRub(spares);
  document.getElementById('roi-labor').textContent = formatRub(labor);
  document.getElementById('roi-payback').textContent = payback;

  // обновить подписи слайдеров
  document.querySelector('output[data-for="roi-hours"]').textContent = hours + ' ч';
  document.querySelector('output[data-for="roi-cost"]').textContent = formatRub(cost) + ' ₽';
  document.querySelector('output[data-for="roi-units"]').textContent = units + ' шт';
}

let roiDebounceTimer;
function initRoi() {
  ['roi-hours', 'roi-cost', 'roi-units'].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('input', () => {
      calculateRoi();
      clearTimeout(roiDebounceTimer);
      roiDebounceTimer = setTimeout(() => {
        if (window.ym) ym(107942912, 'reachGoal', 'roi_calculated');
        if (window.gtag) gtag('event', 'roi_calculated');
      }, 500);
    });
  });
  calculateRoi();
}
document.addEventListener('DOMContentLoaded', initRoi);
```

- [ ] **Step 4: Smoke-проверка**

Открыть главную, найти калькулятор. Подвигать слайдеры — большая цифра меняется мгновенно, разбивка обновляется, окупаемость пересчитывается. На дефолтах:
- 40 × 12 × 50000 × 0.38 = 9 120 000 ₽
- 30 × 80000 × 0.05 = 120 000 ₽
- 40 × 12 × 1500 × 0.25 = 180 000 ₽
- **Total ≈ 9 420 000 ₽/год**, окупаемость ≈ 1 месяц.

На мобильных (375px) — две колонки складываются в одну.

- [ ] **Step 5: Commit**

```bash
git add landing/index.html
git commit -m "feat(roi): add interactive ROI calculator section"
```

---

## Task 12: Аккордеон «Как считаются эти цифры»

**Files:**
- Modify: `landing/index.html` (сразу после секции `#roi-calculator`)

- [ ] **Step 1: Вставить HTML**

```html
<section id="roi-methodology" class="methodology-section">
  <div class="container">
    <h2 class="section-title">Как считаются эти цифры</h2>
    <p class="section-subtitle">Прозрачная методология калькулятора и бенчмарков</p>

    <div class="methodology-list">
      <details>
        <summary>Откуда −38% сокращения простоев?</summary>
        <p>Цифра основана на агрегированной статистике 50+ внедрений CMMS на российских машиностроительных и пищевых предприятиях. Главные источники сокращения: переход с реактивного обслуживания на плановое, мгновенная фиксация заявок через мобильное приложение, история ремонтов в одном месте. Подробнее — в статье <a href="/blog/zachem-avtomatizirovat-toir/">«Зачем автоматизировать ТОиР»</a>.</p>
      </details>
      <details>
        <summary>Как считается экономия на запчастях (5%)?</summary>
        <p>5% — консервативная оценка. Возникает за счёт устранения дублирующих закупок (одна и та же деталь покупается дважды разными цехами), снижения аварийных закупок по завышенной цене и оптимизации страховых запасов. Средняя стоимость 80 000 ₽ на единицу/год — медиана по парку 50–500 единиц.</p>
      </details>
      <details>
        <summary>Почему окупаемость 4–8 месяцев?</summary>
        <p>При типовых параметрах среднего завода (40 ч простоев/мес, 50 000 ₽/час, 30 единиц критичного оборудования) годовая экономия ≈ 9 млн ₽. При стоимости эТОИР 90 000 ₽/мес (1 080 000 ₽/год) окупаемость считается как годовой_расход / годовая_экономия × 12. На малых парках срок длиннее, на крупных — короче.</p>
      </details>
      <details>
        <summary>Источники бенчмарков (1500 ₽/час, 80 000 ₽/ед.)?</summary>
        <p>1500 ₽/час — средняя полная стоимость часа слесаря на промпредприятии в РФ (оклад + соцпакет + накладные) на 2025 год. 80 000 ₽/ед./год — медиана годового расхода на запчасти и расходники по статистике клиентов в машиностроении и металлургии. Цифры консервативные — на тяжёлой технике расходы выше.</p>
      </details>
      <details>
        <summary>Методология калькулятора</summary>
        <p>Расчёт строится по трём независимым каналам экономии: простои × коэффициент сокращения, запчасти × коэффициент оптимизации, трудозатраты × коэффициент перераспределения. Калькулятор не учитывает разовые эффекты (списание старых запасов, продажа избыточного оборудования) и нематериальные выгоды (репутация, удержание персонала). Подробный разбор расчётов — в статье <a href="/blog/cmms-vs-excel/">«эТОИР vs Excel»</a>.</p>
      </details>
    </div>
  </div>
</section>
```

- [ ] **Step 2: Добавить CSS**

```css
.methodology-section { padding: 80px 0; background: #fff; }
.methodology-list { max-width: 800px; margin: 48px auto 0; }
.methodology-list details {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  margin-bottom: 12px;
  padding: 20px 24px;
  background: #fff;
  transition: box-shadow 0.2s;
}
.methodology-list details[open] { box-shadow: 0 4px 12px rgba(0,0,0,0.04); }
.methodology-list summary {
  cursor: pointer;
  font-weight: 600;
  color: #1e293b;
  list-style: none;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.methodology-list summary::after {
  content: '+';
  font-size: 1.5rem;
  color: #2563eb;
  transition: transform 0.2s;
}
.methodology-list details[open] summary::after { content: '−'; }
.methodology-list summary::-webkit-details-marker { display: none; }
.methodology-list p { margin: 16px 0 0; line-height: 1.7; color: #475569; }
```

- [ ] **Step 3: Соединить аккордеон с кнопкой «Откуда эти цифры?» из Task 11**

В тот же `<script>` дописать:

```js
const methodologyLink = document.querySelector('.roi-methodology-link');
if (methodologyLink) {
  methodologyLink.addEventListener('click', () => {
    const target = document.getElementById('roi-methodology');
    if (target) target.scrollIntoView({ behavior: 'smooth' });
    const firstDetails = target?.querySelector('details');
    if (firstDetails) firstDetails.open = true;
  });
}
```

- [ ] **Step 4: Smoke-проверка**

Кликнуть «Откуда эти цифры?» в калькуляторе → плавный скролл, первый пункт раскрыт. Открыть/закрыть каждый из 5 пунктов вручную. Ссылки внутри пунктов кликабельны.

- [ ] **Step 5: Commit**

```bash
git add landing/index.html
git commit -m "feat(roi): add methodology accordion under ROI calculator"
```

---

## Task 13: Слайдшоу-демо из 4 скриншотов

**Files:**
- Modify: `landing/index.html` (вставить после блока «Всё оборудование на карте цеха» ~стр. 3675, перед «Три шага до результата»)

- [ ] **Step 1: Вставить HTML**

```html
<section id="product-demo" class="demo-section">
  <div class="container">
    <h2 class="section-title">Так выглядит эТОИР в работе</h2>
    <p class="section-subtitle">Главные экраны системы — без записи на демо</p>

    <div class="slideshow" data-autoplay="6000">
      <div class="slideshow-track">
        <div class="slide active">
          <img src="images/top-dash.png" alt="Дашборд эТОИР: статус парка оборудования в реальном времени" width="1920" height="1200" loading="lazy" decoding="async">
          <div class="slide-caption">Дашборд: статус парка в реальном времени</div>
        </div>
        <div class="slide">
          <img src="images/orders.png" alt="Наряд-заказы в эТОИР: от заявки до закрытия" width="1920" height="1200" loading="lazy" decoding="async">
          <div class="slide-caption">Наряд-заказы: от заявки до закрытия</div>
        </div>
        <div class="slide">
          <img src="images/assets.png" alt="Учёт оборудования и история ремонтов в эТОИР" width="1920" height="1200" loading="lazy" decoding="async">
          <div class="slide-caption">Учёт оборудования и история ремонтов</div>
        </div>
        <div class="slide">
          <img src="images/AI.png" alt="AI-подсказки в эТОИР: что починить в первую очередь" width="1920" height="1200" loading="lazy" decoding="async">
          <div class="slide-caption">AI-подсказки: что починить в первую очередь</div>
        </div>
      </div>
      <button class="slideshow-nav slideshow-prev" aria-label="Предыдущий слайд">‹</button>
      <button class="slideshow-nav slideshow-next" aria-label="Следующий слайд">›</button>
      <div class="slideshow-dots">
        <button class="slideshow-dot active" data-index="0" aria-label="Слайд 1"></button>
        <button class="slideshow-dot" data-index="1" aria-label="Слайд 2"></button>
        <button class="slideshow-dot" data-index="2" aria-label="Слайд 3"></button>
        <button class="slideshow-dot" data-index="3" aria-label="Слайд 4"></button>
      </div>
    </div>
  </div>
</section>
```

- [ ] **Step 2: Добавить CSS**

```css
.demo-section { padding: 80px 0; background: #f8fafc; }
.slideshow {
  position: relative;
  max-width: 1100px;
  margin: 48px auto 0;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 30px 80px rgba(0,0,0,0.12);
  background: #fff;
}
.slideshow-track { position: relative; aspect-ratio: 16 / 10; }
.slide {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 0.5s ease;
  pointer-events: none;
}
.slide.active { opacity: 1; pointer-events: auto; }
.slide img { width: 100%; height: 100%; object-fit: cover; display: block; }
.slide-caption {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px 24px;
  background: linear-gradient(to top, rgba(0,0,0,0.7), transparent);
  color: #fff;
  font-weight: 500;
}
.slideshow-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: none;
  background: rgba(255,255,255,0.9);
  color: #1e293b;
  font-size: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.slideshow-prev { left: 16px; }
.slideshow-next { right: 16px; }
.slideshow-dots {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
}
.slideshow-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: none;
  background: rgba(255,255,255,0.5);
  cursor: pointer;
  transition: background 0.2s, transform 0.2s;
}
.slideshow-dot.active { background: #fff; transform: scale(1.3); }
@media (max-width: 768px) {
  .slideshow { border-radius: 12px; }
  .slideshow-nav { width: 36px; height: 36px; font-size: 18px; }
}
```

- [ ] **Step 3: Добавить JS**

```js
function initSlideshow() {
  const root = document.querySelector('.slideshow');
  if (!root) return;
  const slides = root.querySelectorAll('.slide');
  const dots = root.querySelectorAll('.slideshow-dot');
  const prev = root.querySelector('.slideshow-prev');
  const next = root.querySelector('.slideshow-next');
  const interval = parseInt(root.dataset.autoplay || '0', 10);
  let current = 0;
  let timer = null;

  function show(i) {
    current = (i + slides.length) % slides.length;
    slides.forEach((s, idx) => s.classList.toggle('active', idx === current));
    dots.forEach((d, idx) => d.classList.toggle('active', idx === current));
  }

  function start() {
    if (interval > 0 && window.innerWidth >= 768) {
      timer = setInterval(() => show(current + 1), interval);
    }
  }
  function stop() { if (timer) { clearInterval(timer); timer = null; } }

  prev.addEventListener('click', () => { show(current - 1); stop(); start(); });
  next.addEventListener('click', () => { show(current + 1); stop(); start(); });
  dots.forEach(d => d.addEventListener('click', () => {
    show(parseInt(d.dataset.index, 10));
    stop(); start();
  }));
  root.addEventListener('mouseenter', stop);
  root.addEventListener('mouseleave', start);

  // touch-свайп для мобильных
  let touchStartX = 0;
  root.addEventListener('touchstart', e => { touchStartX = e.touches[0].clientX; }, { passive: true });
  root.addEventListener('touchend', e => {
    const dx = e.changedTouches[0].clientX - touchStartX;
    if (Math.abs(dx) > 50) show(current + (dx < 0 ? 1 : -1));
  });

  start();
}
document.addEventListener('DOMContentLoaded', initSlideshow);
```

- [ ] **Step 4: Smoke-проверка**

Открыть главную, проскроллить до слайдшоу. На desktop: автопрокрутка каждые 6 сек, hover паузит, стрелки и дотсы работают. На mobile (DevTools): автопрокрутка выключена, свайп влево/вправо переключает слайды.

Проверить, что 4 скриншота `top-dash.png`, `orders.png`, `assets.png`, `AI.png` действительно лежат в `landing/images/`. Если нет — `git ls-files landing/images/`. Если каких-то нет, попросить пользователя положить недостающие или подменить на существующие (`dash.png` вместо `top-dash.png` и т.д.).

- [ ] **Step 5: Commit**

```bash
git add landing/index.html
git commit -m "feat(demo): add product screenshot slideshow with auto-play and swipe"
```

---

## Task 14: Sticky mobile CTA на главной

**Files:**
- Modify: `landing/index.html`

- [ ] **Step 1: Добавить HTML перед футером**

```html
<div class="sticky-cta-mobile" aria-hidden="true">
  <span class="sticky-cta-text">Бесплатное демо за 30 минут</span>
  <a href="#contact" class="sticky-cta-btn">Записаться</a>
  <button class="sticky-cta-close" aria-label="Закрыть">✕</button>
</div>
```

- [ ] **Step 2: Добавить CSS**

Те же стили, что в Task 6 шаг 6 (`.sticky-cta-mobile`, `.sticky-cta-text`, `.sticky-cta-btn`, `.sticky-cta-close` + медиа-запрос). Если стили уже добавлены в общий блок (а они не должны быть — это новый файл), скопировать сюда.

- [ ] **Step 3: Добавить JS — отдельная функция для главной**

```js
function initStickyCtaMain() {
  const cta = document.querySelector('.sticky-cta-mobile');
  if (!cta) return;
  if (sessionStorage.getItem('sticky-cta-dismissed')) return;

  // Маркер — конец hero-секции
  const hero = document.querySelector('.hero, #hero, [class*="hero"]');
  if (!hero) return;

  const heroBottom = hero.offsetTop + hero.offsetHeight;
  let shown = false;
  window.addEventListener('scroll', () => {
    if (shown) return;
    if (window.scrollY > heroBottom) {
      cta.classList.add('visible');
      cta.setAttribute('aria-hidden', 'false');
      shown = true;
    }
  }, { passive: true });

  cta.querySelector('.sticky-cta-close').addEventListener('click', () => {
    cta.classList.remove('visible');
    cta.setAttribute('aria-hidden', 'true');
    sessionStorage.setItem('sticky-cta-dismissed', '1');
  });

  cta.querySelector('.sticky-cta-btn').addEventListener('click', () => {
    if (window.ym) ym(107942912, 'reachGoal', 'sticky_cta_click');
    if (window.gtag) gtag('event', 'sticky_cta_click');
  });
}
document.addEventListener('DOMContentLoaded', initStickyCtaMain);
```

Селектор `.hero` подобрать после открытия `landing/index.html` — найти класс существующей hero-секции.

- [ ] **Step 4: Smoke-проверка**

DevTools → mobile (375px). Открыть главную, проскроллить ниже hero — внизу появляется плашка. Кнопка «Записаться» ведёт на `#contact`. Кнопка ✕ закрывает, sessionStorage хранит ключ, перезагрузка в той же сессии — плашка не появляется. Открыть новую вкладку в инкогнито — плашка снова появляется.

На desktop (`>768px`) плашка не отображается.

- [ ] **Step 5: Commit**

```bash
git add landing/index.html
git commit -m "feat(ux): add sticky mobile CTA on main page after hero"
```

---

## Task 15: Финальные проверки, метрики, документация

**Files:**
- Modify: `S:\_python_rojects\e-toir-langing\docs\seo-plan.md`

- [ ] **Step 1: Финальная сборка прода**

Запустить локальный сервер из `landing/`. Пройти по чеклисту:

- Главная: 13 FAQ, отрасли (6 карточек), таблица сравнения, ROI-калькулятор работает, аккордеон методологии, слайдшоу с 4 скриншотами, sticky mobile CTA после hero, ссылка на блог в шапке/футере, BreadcrumbList в head.
- `/blog/`: индекс с 3 карточками.
- `/blog/cmms-vs-excel/`: статья, TOC desktop sticky, TOC mobile collapsible, sticky CTA, 3 ссылки на главную, 2 ссылки на другие статьи.
- `/blog/kak-vnedrit-toir-sistemu/`: то же, 7 H2.
- `/blog/zachem-avtomatizirovat-toir/`: то же, 6 H2.
- `/sitemap.xml`: 5 URL.

- [ ] **Step 2: Прогнать главную через Rich Results Test**

`https://search.google.com/test/rich-results` → ввести URL после деплоя ИЛИ скопировать HTML главной. Проверить:
- SoftwareApplication: распознан
- Organization: распознан
- FAQPage: 13 вопросов
- BreadcrumbList: 1 уровень

Проверить аналогично 3 статьи блога: Article + BreadcrumbList без ошибок.

- [ ] **Step 3: Прогнать главную через PageSpeed Insights**

`https://pagespeed.web.dev/` → URL. Цель — Performance ≥ 80 на mobile. Если ниже:
- Проверить лениво ли грузятся скриншоты в слайдшоу (`loading="lazy"` стоит)
- Размеры PNG могут быть избыточны — можно поджать через `tinypng.com` (вручную, в отдельной задаче не в этом плане)

- [ ] **Step 4: Зарегистрировать цели в Я.Метрике и GA4**

В Я.Метрике (id 107942912):
- Цель → JavaScript-событие → имя: `roi_calculated`
- Цель → JavaScript-событие → имя: `sticky_cta_click`

В GA4 (G-DS3D1SLNHD):
- Admin → Events → проверить, что `roi_calculated` и `sticky_cta_click` приходят (после реальных кликов)
- При желании пометить их как Conversions.

- [ ] **Step 5: Отметить выполнение в `docs/seo-plan.md`**

В файле `S:\_python_rojects\e-toir-langing\docs\seo-plan.md` создать новый раздел между «Часть I» и «Часть II»:

```markdown
## Часть I.5. Результаты фазы 2 (выполнено 2026-05-19)

### Перенос фазы 1 в прод (`D:\prod_projects\etoir-landing\landing\`)

- [x] FAQ расширен с 6 до 13 вопросов, JSON-LD `FAQPage` синхронизирован
- [x] Секция «Для каких отраслей» — 6 карточек
- [x] Таблица сравнения эТОИР vs Excel vs 1С:ТОИР (8 строк)
- [x] BreadcrumbList JSON-LD на главной
- [x] Блог: `/blog/` + 3 статьи (cmms-vs-excel, kak-vnedrit-toir-sistemu, zachem-avtomatizirovat-toir)
- [x] sitemap.xml: 5 URL
- [x] Ссылка на блог в шапке и футере главной

### Блок 6. Поведенческие факторы

- [x] **Task 16:** ROI-калькулятор (3-факторный), слайдшоу из 4 реальных скриншотов, аккордеон методологии — всё на главной
- [x] **Task 17:** Sticky TOC (desktop) / collapsible (mobile) в 3 статьях; sticky mobile CTA на главной и в статьях; 3+2 контекстных внутренних ссылок в каждой статье
- [ ] **Task 18:** Email-рассылка и Telegram-канал — отложено (требует бэкенда)

### Цели в аналитике

- [x] Я.Метрика: цели `roi_calculated`, `sticky_cta_click`
- [x] GA4: события `roi_calculated`, `sticky_cta_click`
```

- [ ] **Step 6: Commit документации в S-репо**

```bash
# S не git-репо — этот шаг выполняется только если S превратится в репо.
# Иначе просто сохранить файл.
```

- [ ] **Step 7: Финальный commit в проде**

```bash
cd D:\prod_projects\etoir-landing
git status
# должен показать: всё закоммичено по предыдущим задачам
git log --oneline -20
# проверить, что 14 коммитов на месте
```

---

## Открытые моменты, требующие действий пользователя

1. **Скриншот `AI.png`** — убедиться, что файл существует в `landing/images/`. Если в проде нет AI-экрана, заменить четвёртый слайд на `dash.png` (или другой имеющийся), скорректировав alt и caption.
2. **Класс hero-секции** — узнать точное имя класса для селектора в Task 14 step 3 (`.hero`, `.hero-section`, или другое).
3. **CSS-переменные** — если в проде используются другие имена переменных (`--brand-blue` вместо `--primary` и т.п.), подменить в новых стилях.
4. **Класс `.nav-link`** в шапке (Task 10) — убедиться в существующем имени и подменить, если в проде другое.
5. **Контент статей** — переписать из S, поменяв «e-TOIR» → «эТОИР». Если в S статьи отсутствуют или короче плана — дописать недостающее (целевой объём указан в каждой задаче).
