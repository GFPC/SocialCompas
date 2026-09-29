# 🧭 Социальный Компас (SocialCompass)

Единая цифровая экосистема социального навигатора для **MAX Messenger** и **Telegram MiniApp** — помогает находить скидки, акции, льготы, культурные площадки и социальные программы для **студентов**, **пенсионеров** и **участников СВО** в городах России (Москва, Санкт-Петербург, Новосибирск).

[![Production Status](https://img.shields.io/badge/Production-Live-success)](https://socialcompass.ru)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://docker.com)

---

## 🌐 Production-сервер и ссылки

| Сервис | Ссылка / Адрес |
|--------|----------------|
| **MiniApp (SPA Frontend)** | [https://socialcompass.ru](https://socialcompass.ru) |
| **Backend REST API** | [https://api.socialcompass.ru](https://api.socialcompass.ru) |
| **MAX Messenger Bot** | Поиск в MAX Messenger: **SocialCompass** |

---

## Назначение решения

Сервис **SocialCompass** решает проблему сложного и разрозненного поиска льгот, акций и доступных досуговых мест для социальных категорий граждан (студенты, пенсионеры, участники СВО).
Решение реализовано как чат-бот в **MAX Messenger**, интегрированный с единым веб-приложением (**MiniApp**), предоставляющим интерактивную карту, списки мест, личное избранное и ИИ-гида по акциям.

---

## Основной пользовательский сценарий

1. **Онбординг**: Пользователь открывает чат-бот в MAX Messenger или запускает MiniApp. Проходит 2 быстрых шага: выбор города (Москва, Санкт-Петербург, Новосибирск) и льготной категории (Студенты, Пенсионеры, Участники СВО).
2. **Просмотр каталога**: Пользователь попадает на главный экран со списком мест и акций, отфильтрованных под его профиль. Доступно переключение между режимами «Список» и «Яндекс Карта».
3. **Фильтрация и детали**: Фильтрация по типам площадок (Музеи, Театры, Аквапарки, Боулинг, Котокафе, Спорт). Клик по карточке открывает подробный экран с адресом, графиком работы, информацией о скидке и кнопкой перехода.
4. **Избранное**: Добавление понравившихся мест в личное избранное с изолированным хранением на сервере.
5. **ИИ-Гид (AI Tunnel)**: Пользователь задаёт вопросы ассистенту в чате (например, *«Куда сходить со студенческим в субботу?»*). ИИ отвечает с учётом реальных мест из базы данных. При попытке задать посторонний вопрос (код, математика) ИИ вежливо напоминает о специализации сервиса.
6. **Синхронизация профиля**: При смене города или категории в MiniApp профиль мгновенно обновляется в БД и FSM-контексте чат-бота без повторного прохождения онбординга.

---

## Состав и архитектура решения

```
              ┌──────────────────────────────────────────────┐
              │           Пользовательский интерфейс         │
              │   MAX Messenger Bot / React 18 MiniApp       │
              └──────────────────────┬───────────────────────┘
                                     │
                                     ▼
              ┌──────────────────────────────────────────────┐
              │            FastAPI Unified Backend           │
              │  REST API (/api/v1/) + MAX Bot Listener      │
              └──────┬───────────────────────┬───────────────┘
                     │                       │
                     ▼                       ▼
      ┌─────────────────────────────┐   ┌─────────────────────────────┐
      │   MySQL 8.0 (aiomysql)      │   │     Redis 7 / Memory        │
      │  Места, Профили, Избранное  │   │  FSM состояния чат-бота     │
      └─────────────────────────────┘   └─────────────────────────────┘
                                             │
                                             ▼
                                ┌─────────────────────────────┐
                                │   AI Tunnel (GPT-4o-mini)   │
                                └─────────────────────────────┘
```

---

## Команда для запуска всех локальных компонентов через Docker

Запуск всех компонентов сервиса одной командой:

```bash
docker compose up -d --build
```

*Сборка занимает не более 1-2 минут.*

После запуска доступно:
- **MiniApp (SPA)**: `http://localhost:8000`
- **Swagger UI (Интерактивная документация)**: `http://localhost:8000/docs`
- **OpenAPI 3.0 Спецификация**: `http://localhost:8000/openapi.json`
- **Проверка здоровья (Healthcheck)**: `http://localhost:8000/api/v1/cities`

---

## Необходимые параметры и переменные окружения

Файл параметров окружения `.env.example`:

| Переменная | Описание | Значение по умолчанию |
|------------|----------|-----------------------|
| `MAX_BOT_TOKEN` | Токен бота в MAX Messenger API | `YOUR_MAX_BOT_TOKEN_HERE` |
| `MAX_API_URL` | Базовый URL API MAX Messenger | `https://platform-api2.max.ru` |
| `HOST` | Хост для запуска Uvicorn | `0.0.0.0` |
| `PORT` | Порт приложения | `8000` |
| `MYSQL_HOST` | Хост СУБД MySQL | `mysql` |
| `MYSQL_PORT` | Порт СУБД MySQL | `3306` |
| `MYSQL_USER` | Пользователь БД | `bot_user` |
| `MYSQL_PASSWORD` | Пароль БД | `bot_password` |
| `MYSQL_DB` | Имя базы данных | `socialcompas_db` |
| `REDIS_HOST` | Хост Redis | `redis` |
| `REDIS_PORT` | Порт Redis | `6379` |
| `AITUNNEL_API_KEY` | Ключ доступа к AI Tunnel API | `YOUR_AITUNNEL_API_KEY_HERE` |
| `AITUNNEL_BASE_URL` | Эндпоинт AI Tunnel API | `https://api.aitunnel.ru/v1` |
| `AI_MODEL` | Модель ИИ | `gpt-4o-mini` |
| `CHAT_RATE_LIMIT_PER_MINUTE` | Лимит запросов в минуту к ИИ | `10` |
| `ENABLE_DOCS` | Включить Swagger `/docs` | `true` (для локальной проверки) |

---

## Используемые порты

- `8000`: FastAPI Backend API & MiniApp Web Server
- `3306` / `3307`: MySQL Database
- `6379`: Redis Cache / FSM

---

## Зависимости

- **Python**: `3.11+`
- **Node.js**: `18+` (для сборки фронтенда miniapp)
- **Docker & Docker Compose**: Compose v2+
- **Зафиксированные версии зависимостей**: [`requirements.txt`](requirements.txt) (`fastapi==0.115.0`, `uvicorn==0.32.0`, `pydantic==2.10.0`, `httpx==0.28.1`, `aiomysql==0.2.0`, `redis==5.2.0`, `alembic==1.14.0`).

---

## Внешние сервисы и интеграции

1. **MAX Messenger Platform API** (`https://platform-api2.max.ru`): Получение обновлений пользователя, отправка кнопок и сообщений чат-бота.
2. **AI Tunnel API** (`https://api.aitunnel.ru/v1`): LLM-интеграция для генерации ответов ИИ-гида.
3. **Яндекс Карты API** (`https://api-maps.yandex.ru/2.1/`): Отображение интерактивных геолокационных меток мест на карте.

---

## Описание работы с данными

Данные о скидках и партнерских площадках хранятся в MySQL в таблице `places`.
Базовый каталог поставляется в виде файла Excel в каталоге `data/`. Таблица профилей `user_profiles` и состояний `user_states` обеспечивают изоляцию пользователей и синхронизацию FSM.

---

## Порядок работы с тестовыми данными

Порядок первичной загрузки данных мест в базу:
```bash
docker exec socialcompas_app python scripts/import_excel.py
```
Скрипт импортирует 87 записей проверенных мест и акций по г. Москва, Санкт-Петербург и Новосибирск.

Тестовые аккаунты пользователей зафиксированы в файле [`data/test_accounts.json`](data/test_accounts.json):

| Имя пользователя | Роль | `user_id` | Тестовый город | Категория |
|------------------|------|-----------|----------------|-----------|
| Алексей Иванов | Студент | `998877` | Москва | Студенты |
| Мария Петрова | Пенсионер | `554433` | Санкт-Петербург | Пенсионеры |
| Сергей Сидоров | Участник СВО | `112233` | Новосибирск | Участники СВО |

---

## Пошаговый сценарий проверки

### 1. Запуск автоматического тест-сюита (27 проверок)
```bash
python test_bot.py
```
Проверяет: онбординг, FSM бота, авторизацию HMAC initData, JWT-токены, синхронизацию профилей MiniApp↔Bot, каталог мест, изоляцию избранного и ИИ Guardrails.

### 2. Запуск локального Docker-стека
```bash
cp .env.example .env
docker compose up -d --build
docker exec socialcompas_app python scripts/import_excel.py
```

---

## Примеры ожидаемого поведения системы

### 1. GET `/api/v1/cities` (Список городов)
- **Запрос**: `curl http://localhost:8000/api/v1/cities`
- **Ожидаемый ответ** (`200 OK`):
```json
{
  "ok": true,
  "count": 3,
  "items": [
    {"id": 1, "name": "Москва", "is_active": 1},
    {"id": 2, "name": "Новосибирск", "is_active": 1},
    {"id": 3, "name": "Санкт-Петербург", "is_active": 1}
  ]
}
```

### 2. GET `/api/v1/places?city=Москва&category=Студенты` (Места по категории)
- **Запрос**: `curl "http://localhost:8000/api/v1/places?city=Москва&category=Студенты"`
- **Ожидаемый ответ** (`200 OK`):
```json
{
  "ok": true,
  "count": 10,
  "items": [
    {
      "id": 1,
      "title": "Третьяковская галерея",
      "city": "Москва",
      "category": "Студенты",
      "place_type": "Музей",
      "promo_text": "Студентам очной формы — скидка 50% по студенческому билету.",
      "address": "г. Москва, Лаврушинский пер., 10"
    }
  ]
}
```

### 3. POST `/api/v1/chat` (Тематический вопрос к ИИ-гиду)
- **Запрос**: `curl -X POST http://localhost:8000/api/v1/chat -H "Content-Type: application/json" -d '{"messages": [{"role": "user", "content": "Какие музеи есть со скидкой?"}], "city": "Москва", "category": "Студенты"}'`
- **Ожидаемый ответ** (`200 OK`):
```json
{
  "ok": true,
  "message": "В Москве по студенческому билету вы можете посетить Третьяковскую галерею со скидкой 50%..."
}
```

### 4. POST `/api/v1/chat` (Посторонний вопрос — Guardrail)
- **Запрос**: `curl -X POST http://localhost:8000/api/v1/chat -H "Content-Type: application/json" -d '{"messages": [{"role": "user", "content": "Напиши код на Python"}], "city": "Москва", "category": "Студенты"}'`
- **Ожидаемый ответ** (`200 OK`):
```json
{
  "ok": true,
  "message": "Я — ассистент SocialCompass 🧭 и специализируюсь на поиске мест для отдыха и скидок..."
}
```

---

## Известные ограничения

1. **Swagger UI на Production**: В целях безопасности документация Swagger (`/docs`) **намеренно отключена на боевом сервере** (`ENABLE_DOCS=false`). При локальном запуске через Docker она включена по умолчанию (`ENABLE_DOCS=true`).
2. **Лимит ИИ-запросов (Rate Limiter)**: Во избежание абуза установлен лимит 10 запросов в минуту на IP (`CHAT_RATE_LIMIT_PER_MINUTE=10`).
3. **География MVP**: Каталог мест покрывает 3 крупных города (Москва, Санкт-Петербург, Новосибирск) с динамическим добавлением новых городов в таблице `cities`.

---

## Порядок остановки и повторного запуска решения

### Порядок остановки решения:
```bash
docker compose down
```

### Порядок повторного запуска решения:
```bash
docker compose up -d
```

### Полный перезапуск с очисткой томов:
```bash
docker compose down -v && docker compose up -d --build
```

---

## Спецификации и ссылки на артефакты

- **OpenAPI 3.0 REST Specification**: [`openapi.yaml`](openapi.yaml)
- **Data API Schema Specification**: [`DATA-API.yaml`](DATA-API.yaml)
- **Тестовые аккаунты**: [`data/test_accounts.json`](data/test_accounts.json)
- **Тестовые данные мест**: [`data/test_data.json`](data/test_data.json)
- **Production Сайт (MiniApp SPA)**: [https://socialcompass.ru](https://socialcompass.ru)
- **Production API**: [https://api.socialcompass.ru](https://api.socialcompass.ru)
