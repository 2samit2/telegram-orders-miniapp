# ☕ Artisan Coffee & Bakery — Telegram Order Bot with Mini App

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0)](https://aiogram.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)](https://fastapi.tiangolo.com)

Флагманский проект: Telegram-бот для бизнеса с современным **Mini App (Web App)**
интерфейсом — витрина кофейни «Artisan Coffee & Bakery», каталог товаров, корзина
и мгновенные уведомления менеджеру о новых заказах.

---

## 📖 Описание / Overview

### 🇷🇺 Русский

**Что умеет проект:**

- 🤖 **Telegram-бот (aiogram 3)** — команда `/start` с кнопкой `web_app` для
  открытия витрины прямо в Telegram; команда `/admin` для менеджера — просмотр
  последних 5 заказов с обновлением по кнопке.
- 🖥 **Mini App (Web App)** — адаптивный мобильный каталог с тремя категориями
  (Кофе, Десерты, Завтраки), карточками товаров, счётчиками «+»/«−», плавающей
  корзиной и интеграцией с `Telegram.WebApp.MainButton`.
- 🎨 **Темы Telegram** — интерфейс автоматически подстраивается под светлую и
  тёмную темы клиента через CSS-переменные `--tg-theme-*`.
- 📦 **Оформление заказа** — модальное окно с вводом адреса/столика, телефона,
  имени и комментария; заказ сохраняется в SQLite.
- 🔔 **Уведомление менеджеру** — отформатированное сообщение в чат
  администратора: номер заказа, имя клиента, username, состав, сумма, дата.
- 🔐 **Безопасность** — проверка подписи `initData` (HMAC-SHA256) и расчёт
  суммы заказа по ценам из базы (клиент не может подделать цену).
- 🌐 **Standalone-режим** — витрина полностью работает в обычном десктопном
  браузере с моковыми данными пользователя (удобно для разработки и демо).
- 🐳 **Docker** — запуск одной командой через `docker compose up`.

**Стек:** Python 3.11+, aiogram 3, FastAPI + Uvicorn, aiosqlite (SQLite),
Pydantic / pydantic-settings, HTML5 + Tailwind CSS (CDN) + Vanilla JS.

### 🇬🇧 English

A production-ready Telegram bot for a demo coffee shop with a modern Web App
(Mini App) storefront: product catalogue, interactive cart, checkout and
instant order notifications for the shop manager.

- **Bot (aiogram 3):** `/start` greets the user with a `web_app` button;
  `/admin` shows the 5 most recent orders to the manager.
- **Mini App:** responsive mobile-first catalogue (Coffee, Desserts, Breakfast),
  quantity steppers, floating cart, `Telegram.WebApp.MainButton` integration.
- **Theming:** automatic light/dark Telegram themes via `--tg-theme-*`
  CSS variables.
- **Checkout:** modal with address/table, phone, name and comment; the order is
  stored in SQLite.
- **Notifications:** the manager receives a richly formatted message with order
  id, customer name, username, items, total and timestamp.
- **Security:** `initData` HMAC-SHA256 signature verification; the total is
  always recomputed from database prices.
- **Standalone mode:** the storefront is fully testable in a desktop browser
  with mock user data.
- **Docker:** run everything with a single `docker compose up --build`.

---

## 🗂 Структура проекта / Project structure

```text
telegram-order-bot/
├── app/
│   ├── bot/
│   │   ├── handlers.py       # /start, /admin, admin callbacks
│   │   └── keyboards.py      # web_app button, admin refresh button
│   ├── database/
│   │   ├── db.py             # aiosqlite wrapper (products, orders)
│   │   └── seed.py           # automatic seeding of demo products
│   ├── static/
│   │   ├── index.html        # Mini App page (Tailwind + telegram-web-app.js)
│   │   ├── app.js            # catalogue, cart, checkout logic
│   │   └── style.css         # Telegram theme variables + fallbacks
│   ├── web/
│   │   └── routes.py         # GET /api/products, POST /api/order
│   ├── config.py             # pydantic-settings configuration
│   └── models.py             # Pydantic schemas
├── main.py                   # FastAPI + aiogram polling entry point
├── requirements.txt          # pinned dependency versions
├── Dockerfile                # python:3.11-slim image
├── docker-compose.yml        # one-command launch
├── .env.example              # environment template
├── .gitignore
└── README.md
```

---

## 🚀 Быстрый старт / Quick start

### 🇷🇺 Запуск локально (Python)

1. **Клонируйте проект и создайте виртуальное окружение:**

   ```bash
   git clone <repo-url> telegram-order-bot
   cd telegram-order-bot
   python3.11 -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Создайте файл `.env` из шаблона:**

   ```bash
   cp .env.example .env
   ```

3. **Запустите приложение:**

   ```bash
   python main.py
   ```

4. Откройте **http://localhost:8000** — витрина работает в standalone-режиме
   (можно тестировать в браузере без Telegram). Каталог и оформление заказа
   полностью функциональны; уведомление менеджеру отправляется, только если
   указаны валидные `BOT_TOKEN` и `ADMIN_ID`.

### 🇷🇺 Запуск через Docker

```bash
cp .env.example .env    # заполните BOT_TOKEN и ADMIN_ID
docker compose up --build -d
```

Приложение поднимется на **http://localhost:8000**, база SQLite будет
храниться в docker-томе `sqlite-data`.

### 🇬🇧 Local run (Python)

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py          # open http://localhost:8000
```

### 🇬🇧 Docker run

```bash
cp .env.example .env    # fill in BOT_TOKEN and ADMIN_ID
docker compose up --build -d
```

---

## 🤖 Настройка бота через BotFather / Bot setup

### 🇷🇺 Пошаговая инструкция

1. **Создайте бота.** Напишите [@BotFather](https://t.me/BotFather) команду:

   ```
   /newbot
   ```

   Укажите имя (например, `Artisan Coffee & Bakery`) и username
   (например, `artisan_coffee_bot`). BotFather выдаст **токен** —
   скопируйте его в `.env` → `BOT_TOKEN`.

2. **Узнайте свой ID.** Напишите [@userinfobot](https://t.me/userinfobot) —
   он пришлёт ваш числовой ID. Запишите его в `.env` → `ADMIN_ID`.

3. **(Для Mini App) Опубликуйте Web App по HTTPS.** Telegram требует
   публичный HTTPS-URL. Варианты:

   - VPS + домен + reverse-proxy (nginx/Caddy) с TLS-сертификатом;
   - туннель (ngrok, Cloudflare Tunnel) для отладки.

4. **Настройте кнопку Menu Button (опционально).** В BotFather:

   ```
   /setmenubutton → выбрать бота → указать HTTPS-URL витрины
   ```

   После этого витрина открывается из меню бота одним нажатием.

5. **Пропишите `WEBAPP_URL`.** В `.env` укажите публичный HTTPS-URL:

   ```env
   WEBAPP_URL=https://your-domain.example.com/
   ```

   Кнопка в `/start` автоматически станет типом `web_app` (открывает Mini App
   внутри Telegram). Если `WEBAPP_URL` пуст — бот покажет обычную URL-кнопку
   для локальной разработки.

6. **Напишите боту `/start`** и нажмите «🛍 Открыть витрину».

### 🇬🇧 Step-by-step

1. `/newbot` in [@BotFather](https://t.me/BotFather) → copy the token to `.env` (`BOT_TOKEN`).
2. Get your numeric ID from [@userinfobot](https://t.me/userinfobot) → `ADMIN_ID`.
3. Publish the app behind HTTPS (VPS + reverse proxy, or a tunnel for debug).
4. Optionally `/setmenubutton` in BotFather to pin the storefront to the bot menu.
5. Set `WEBAPP_URL=https://your-domain.example.com/` in `.env`.
6. Send `/start` to the bot and tap “🛍 Открыть витрину”.

---

## 🔌 API

| Метод | Путь            | Описание / Description                                     |
|-------|-----------------|------------------------------------------------------------|
| GET   | `/api/products` | Каталог товаров из БД / product catalogue from the DB      |
| POST  | `/api/order`    | Оформить заказ / place an order (→ SQLite + admin notify)  |
| GET   | `/`             | Mini App страница / the Web App page                       |

**Пример / example:**

```bash
curl http://localhost:8000/api/products | head

curl -X POST http://localhost:8000/api/order \
  -H "Content-Type: application/json" \
  -d '{"items":[{"product_id":1,"title":"Капучино","price":260,"quantity":2}],
       "address":"столик №7","comment":"без сахара","guest_name":"Тест"}'
```

POST `/api/order` принимает заголовок `X-Init-Data` с подписанными
Telegram-данными; итоговая сумма всегда пересчитывается по ценам из базы.

---

## 🛠 Технические решения / Implementation notes

- **Один процесс — два сервиса.** `main.py` поднимает FastAPI (Uvicorn) и
  в фоне запускает long-polling aiogram — не нужен отдельный процесс для бота
  и вебхуки.
- **`dispatcher["settings"]` / `dispatcher["db"]`** — DI-механизм aiogram для
  передачи зависимостей в хэндлеры.
- **`app.state`** — FastAPI хранит общие объекты (`db`, `bot`, `settings`)
  и раздаёт их через `Depends`.
- **WAL-режим SQLite** — параллельные чтения без блокировок.
- **Сидинг** — 12 демо-товаров добавляются только при пустой таблице.
- **Валидация initData** — точный алгоритм из документации Telegram
  (`HMAC-SHA256` c ключом `HMAC("WebAppData", bot_token)`).

---

## 📸 Скриншоты / Screenshots

> Добавьте свои скриншоты в папку `assets/` и перечислите их здесь
> (папка `assets/` в `.gitignore`, чтобы не раздувать репозиторий).

| Витрина (светлая) | Витрина (тёмная) | Корзина | Уведомление менеджеру |
|---|---|---|---|
| `assets/catalog-light.png` | `assets/catalog-dark.png` | `assets/cart.png` | `assets/admin-notify.png` |

---

## 📄 Лицензия / License

MIT — свободно используйте как шаблон для своих коммерческих Telegram-ботов
с Mini App.
[Запись экрана_20261005_124725.webm](https://github.com/user-attachments/assets/ebe4ce4c-0381-4cab-971e-4080812e0252)
