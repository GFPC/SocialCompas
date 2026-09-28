# 🧭 Экосистема «Социальный Компас» (SocialCompass)

Единая цифровая экосистема социального навигатора для **MAX Messenger** и **Telegram MiniApp**, разработанная для поиска скидок, акций, льгот, культурных площадок и социальных программ для **студентов**, **пенсионеров** и **участников СВО** в городах России (Москва, Санкт-Петербург, Новосибирск).

[![Production Status](https://img.shields.io/badge/Production-Live-success)](https://socialcompass.ru)
[![API Docs](https://img.shields.io/badge/OpenAPI-Swagger-blue)](https://api.socialcompass.ru/docs)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev)

---

## 🌟 Ключевые возможности

1. **Telegram & MAX WebApp MiniApp**:
   * Адаптивный веб-интерфейс в фирменной гамме MAX Messenger (фиолетово-синий градиент).
   * Выбор города и категории благополучателя на стартовом онбординге.
   * Фильтрация мест по типам (Музеи, Театры, Аквапарки, Боулинг, Кофейни, Спорт и т.д.).
   * Интерактивная карта площадок и быстрый просмотр детальных карточек.
   * Избранное и личные списки мест.

2. **Умный ИИ-Гид (AI Tunnel + gpt-4o-mini)**:
   * Персональный ассистент по скидкам с динамическим обогащением контекста из базы данных MySQL.
   * **Строгий режим безопасности (Guardrails)**: ИИ отвечает *только* на тематические вопросы о льготах и местах и отказывает при попытках абуза или посторонних запросах.
   * **Лимитер запросов (Rate Limiter)**: Ограничение максимум 10 запросов в минуту на пользователя/IP для предотвращения перерасхода ресурсов.

3. **MAX Messenger Бот & Симулятор**:
   * Поддержка двух способов подключения к MAX API: **Webhook** и **Long-Polling**.
   * Локальный интерактивный веб-симулятор (`--sim`) для тестирования диалогов без реального токена.

4. **Высокий уровень безопасности**:
   * Строгая аутентификация через проверку HMAC-SHA256 подписи `initData` мессенджера.
   * Бесшовный доступ к эндпоинтам профиля и избранного только по защищенному **Bearer JWT токену**.

---

## 🛠 Технологический стек

* **Backend**: Python 3.11, FastAPI, Uvicorn, Pydantic v2, HTTPX, PyJWT.
* **Database & ORM**: MySQL 8.0 (`aiomysql`), Alembic (миграции), SQLAlchemy.
* **Caching & FSM**: Redis 7 (`redis-py`).
* **Frontend**: React 18, Vite, Tailwind CSS / Custom UI, Lucide Icons.
* **AI & LLM Integration**: AI Tunnel API (`gpt-4o-mini`).
* **Infrastructure**: Docker, Docker Compose, Nginx, Certbot SSL (HTTPS).

---

## 📁 Структура проекта

```
SocialCompas/
├── api/                   # REST API роутеры FastAPI (v1: places, profile, favorites, chat, auth)
├── core/                  # Авторизация, JWT токены, валидация HMAC initData
├── data/                  # Импортируемые данные Excel и тестовые наборы (test_accounts.json, test_data.json)
├── fsm/                   # Хранилище состояний бота (Redis / MySQL / Memory)
├── miniapp/               # Исходный код React MiniApp (Vite + JSX + CSS)
├── models/                # Pydantic и SQLAlchemy схемы данных
├── scripts/               # Скрипты импорта Excel, симулятора, автодеплоя и Nginx
├── storage/               # Асинхронные пулы MySQL (aiomysql) и Redis
├── test_bot.py            # Полный автоматический тест-сюит бэкенда и безопасности
├── config.py              # Загрузка и валидация конфигурации (.env)
├── main.py                # Единая точка входа backend и бота
├── docker-compose.yml     # Инфраструктура БД (MySQL + Redis) для разработки
├── docker-compose.prod.yml# Production контейнеризация (FastAPI + MySQL + Redis)
├── openapi.yaml           # Полная OpenAPI 3.0 спецификация REST API
├── DATA-API.yaml          # Спецификация структур данных и схем БД
├── requirements.txt       # Зафиксированные версии зависимостей Python (==)
├── .dockerignore          # Исключения для сборки Docker образов
├── .env.example           # Шаблон переменных окружения без секретов
└── README.md              # Документация проекта
```

---

## 🚀 Быстрый запуск через Docker Compose

### 1. Клонирование репозитория и настройка окружения

```bash
git clone https://github.com/GFPC/SocialCompas.git
cd SocialCompas

# Создайте .env файл из шаблона
cp .env.example .env
```

Заполните переменные окружения в `.env` (при необходимости):
```env
MAX_BOT_TOKEN=YOUR_MAX_BOT_TOKEN_HERE
AITUNNEL_API_KEY=YOUR_AITUNNEL_API_KEY_HERE
MYSQL_PASSWORD=bot_password
```

### 2. Запуск проекта в Docker

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

После запуска контейнеров:
* **MiniApp веб-версия**: `http://localhost:8000`
* **Swagger UI (Интерактивная документация)**: `http://localhost:8000/docs`
* **OpenAPI 3.0 YAML спецификация**: `http://localhost:8000/openapi.json`

---

## 🧪 Запуск автоматических тестов

В проекте предустановлен полный интеграционный тест-сюит, проверяющий:
* Корректность онбординга и сценариев Miro.
* Валидацию HMAC-SHA256 подписи WebApp `initData`.
* Выдачу и отклонение поддельных JWT-токенов.
* Ограничение неавторизованного доступа (401 Unauthorized).
* Интеграцию с ИИ-ассистентом и отказ от ответов на посторонние вопросы.

Для запуска тестов выполните:

```bash
python test_bot.py
```

---

## 📄 Спецификации API и данные

1. **OpenAPI 3.0 REST Specification**: [`openapi.yaml`](openapi.yaml)
2. **Data API Schema Specification**: [`DATA-API.yaml`](DATA-API.yaml)
3. **Тестовые аккаунты**: [`data/test_accounts.json`](data/test_accounts.json)
4. **Тестовый каталог мест**: [`data/test_data.json`](data/test_data.json)

---

## 🌐 Production сервер

* **Основной сайт (MiniApp SPA)**: [https://socialcompass.ru](https://socialcompass.ru)
* **API Субдомен**: [https://api.socialcompass.ru/docs](https://api.socialcompass.ru/docs)
