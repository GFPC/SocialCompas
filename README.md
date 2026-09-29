# 🧭 Социальный Компас (SocialCompass)

Единая цифровая экосистема социального навигатора для **MAX Messenger** и **Telegram MiniApp** — помогает находить скидки, акции, льготы, культурные площадки и социальные программы для **студентов**, **пенсионеров** и **участников СВО** в городах России (Москва, Санкт-Петербург, Новосибирск).

[![Production Status](https://img.shields.io/badge/Production-Live-success)](https://socialcompass.ru)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://docker.com)

---

## 🌐 Production

| Сервис | Адрес |
|--------|-------|
| MiniApp (SPA) | [https://socialcompass.ru](https://socialcompass.ru) |
| API Backend | [https://api.socialcompass.ru](https://api.socialcompass.ru) |
| MAX Bot | Поиск в MAX Messenger: **SocialCompass** |

> **Примечание для жюри:** Swagger UI намеренно **отключён на production**-сервере в целях безопасности. При локальном запуске через `docker compose up` документация доступна по адресу `http://localhost:8000/docs`.

---

## 🌟 Ключевые возможности

1. **MAX Messenger MiniApp + Telegram WebApp**
   - Онбординг: выбор города и категории льготника
   - Каталог мест и акций с интерактивной Яндекс Картой
   - Фильтрация по типам мест (Музеи, Театры, Аквапарки, Боулинг, и др.)
   - Избранное — каждый пользователь имеет свой изолированный список
   - Синхронизация профиля: смена города/категории мгновенно отражается и в боте

2. **ИИ-Гид (AI Tunnel / GPT-4o-mini)**
   - Персональный ассистент с динамическим контекстом из базы данных
   - Отвечает на вопросы о досуге, скидках и местах; вежливо отказывает на посторонние запросы
   - История диалога сохраняется (последние 10 сообщений)
   - Rate Limiter: 10 запросов/минуту на IP

3. **MAX Messenger Bot**
   - Long-Polling и Webhook режимы
   - FSM (конечный автомат): Redis → MySQL → Memory fallback
   - Синхронизация профиля с MiniApp по `user_id`

4. **Безопасность**
   - HMAC-SHA256 валидация `initData` MAX/Telegram
   - JWT токены (Bearer) для защищённых эндпоинтов
   - Swagger/ReDoc **отключён на production** (`ENABLE_DOCS=false`)

---

## 🛠 Технологический стек

| Слой | Технологии |
|------|-----------|
| Backend | Python 3.11, FastAPI, Uvicorn, Pydantic v2, HTTPX |
| Database | MySQL 8.0 (aiomysql), Alembic, SQLAlchemy |
| Cache / FSM | Redis 7 (redis-py) |
| Frontend | React 18, Vite, Lucide Icons, Яндекс Карты API |
| AI | AI Tunnel API (GPT-4o-mini) |
| Infrastructure | Docker, Docker Compose, Nginx, Certbot/SSL |

---

## 📁 Структура проекта

```
SocialCompas/
├── api/                    # REST API роутеры (places, profile, favorites, chat, auth)
├── core/                   # JWT авторизация, HMAC initData валидация
├── data/                   # Каталог мест (Excel), тестовые аккаунты
├── fsm/                    # FSM хранилище (Redis / MySQL / Memory)
├── handlers/               # Обработчики событий MAX Bot (FSM логика)
├── miniapp/                # React MiniApp (Vite + JSX)
├── models/                 # Pydantic / SQLAlchemy модели
├── scripts/                # Скрипты импорта, деплоя, Nginx конфиг
├── storage/                # Async MySQL пул (aiomysql), Redis клиент
├── transport/              # MAX Messenger API клиент
├── alembic/                # Миграции БД
├── test_bot.py             # Полный тест-сюит (6 наборов тестов)
├── config.py               # Конфигурация (.env)
├── main.py                 # Точка входа (FastAPI + Bot)
├── Dockerfile              # Docker образ с healthcheck
├── docker-compose.yml      # Локальный стек (app + MySQL + Redis)
├── docker-compose.prod.yml # Production стек
├── openapi.yaml            # OpenAPI 3.0 спецификация
└── .env.example            # Шаблон переменных окружения
```

---

## 🚀 Быстрый запуск для жюри (Docker)

### 1. Клонировать и настроить окружение

```bash
git clone https://github.com/GFPC/SocialCompas.git
cd SocialCompas
cp .env.example .env
```

Отредактируйте `.env` при необходимости (минимально — укажите токен бота и AI ключ):

```env
MAX_BOT_TOKEN=ваш_токен_бота
AITUNNEL_API_KEY=ваш_ключ_aitunnel
```

### 2. Запустить весь стек одной командой

```bash
docker compose up -d --build
```

Через ~20 секунд доступны:

| Сервис | URL |
|--------|-----|
| MiniApp (SPA) | http://localhost:8000 |
| REST API | http://localhost:8000/api/v1/ |
| Swagger UI | http://localhost:8000/docs |
| Города | http://localhost:8000/api/v1/cities |
| Категории | http://localhost:8000/api/v1/categories |

### 3. Загрузить данные о местах (Excel → MySQL)

```bash
docker exec socialcompas_app python scripts/import_excel.py
```

---

## 🧪 Запуск тестов

```bash
python test_bot.py
```

Тест-сюит включает **6 наборов** (27 проверок):

| # | Набор | Проверяет |
|---|-------|-----------|
| 1 | Bot FSM Flow | Онбординг, навигация, смена профиля |
| 2 | API Security | JWT, HMAC, 401 на защищённых роутах, Swagger отключён |
| 3 | Profile Sync | Синхронизация города/категории между MiniApp и Bot |
| 4 | Places Catalog | Фильтрация мест по городу/категории, 404 для несуществующих |
| 5 | Favorites Isolation | Изоляция избранного: пользователь видит только свои места |
| 6 | AI Chat | Ответы на тематические вопросы, отказ от посторонних, rate limiting |

---

## 📄 API Документация

- **OpenAPI 3.0 спецификация**: [`openapi.yaml`](openapi.yaml)
- **Схемы данных**: [`DATA-API.yaml`](DATA-API.yaml)
- **Тестовые аккаунты**: [`data/test_accounts.json`](data/test_accounts.json)
- **Тестовый каталог**: [`data/test_data.json`](data/test_data.json)

---

## 🔑 Тестовые аккаунты

| Имя | user_id | Город | Категория |
|-----|---------|-------|-----------|
| Алексей Иванов | 998877 | Москва | Студенты |
| Мария Петрова | 554433 | Санкт-Петербург | Пенсионеры |
| Сергей Сидоров | 112233 | Новосибирск | Участники СВО |
