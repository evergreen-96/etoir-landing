# Spec: TG-уведомления о заявках и поля согласия

**Дата:** 2026-04-13
**Статус:** Approved

## Цель

1. Отправлять Telegram-уведомление при каждой новой заявке с лендинга.
2. Фиксировать в БД согласие пользователя с политикой конфиденциальности и согласие на маркетинговые рассылки.

---

## 1. База данных

Миграция таблицы `responses` — два новых поля:

```sql
ALTER TABLE responses ADD COLUMN consent_privacy   INTEGER NOT NULL DEFAULT 0;
ALTER TABLE responses ADD COLUMN consent_marketing INTEGER NOT NULL DEFAULT 0;
```

`1` = согласие дано, `0` = не дано. `consent_privacy` всегда `1` (API валидирует на уровне Pydantic).

`db.py` — изменения:
- `save_response` принимает `consent_privacy: bool`, `consent_marketing: bool`
- INSERT включает оба поля
- `get_all_responses` возвращает их (автоматически, через `SELECT *`)

---

## 2. FastAPI API

### Переменные окружения (`.env`)

```
TG_BOT_TOKEN=<token>
TG_CHAT_ID=<chat_id>
```

### `ResponseIn` (Pydantic)

```python
consent_privacy:   bool = Field(..., description="Обязательное согласие с политикой")
consent_marketing: bool = False
```

Валидация: если `consent_privacy=False` → HTTP 422.

### POST `/api/responses/`

1. Валидирует `consent_privacy == True` (иначе 422).
2. Сохраняет заявку в SQLite.
3. Ставит в очередь `BackgroundTask` — отправка TG-сообщения.
4. Возвращает `{"ok": True}`.

TG-уведомление не блокирует ответ. Если Telegram недоступен — заявка уже сохранена, ошибка логируется в stderr.

### Формат TG-сообщения

```
📋 Новая заявка

Имя: {name}
Компания: {company}
Email: {email}
Телефон: {phone}
Должность: {position или —}
Комментарий: {comment или —}

Дата: {created_at UTC}
Согласие на рассылку: ✅ / ❌
```

Отправка через `httpx.AsyncClient.post` на `https://api.telegram.org/bot{TOKEN}/sendMessage`.

---

## 3. Frontend (landing/index.html)

Чекбоксы уже присутствуют в HTML (`#consentCheck`, `#marketingCheck`) и валидируются перед отправкой.

Нужна только правка в `fetch` body — привести имена полей к контракту API:

```js
// было:
marketing: form.querySelector('#marketingCheck').checked,

// стало:
consent_privacy:   true,   // всегда true (форма не отправится без этого чекбокса)
consent_marketing: form.querySelector('#marketingCheck').checked,
```

---

## 4. Admin-панель (`/admin/`)

Таблица расширяется двумя колонками: **Политика** и **Рассылка** (✅/❌).
CSV-экспорт включает `consent_privacy` и `consent_marketing`.

---

## 5. Конфигурация

`.env.example` дополняется:
```
TG_BOT_TOKEN=
TG_CHAT_ID=
```

---

## 6. Что вне scope

- Повторная отправка уведомления при сбое TG (fire-and-forget).
- Email-уведомления.
- Пагинация в `/admin/`.
