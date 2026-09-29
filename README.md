# 🧭 Социальный Компас (SocialCompass)

Единая цифровая экосистема социального навигатора для **MAX Messenger** и **Telegram MiniApp** — помогает находить скидки, акции, льготы, культурные площадки и социальные программы для **студентов**, **пенсионеров** и **участников СВО** в городах России (Москва, Санкт-Петербург, Новосибирск).

[![Production Status](https://img.shields.io/badge/Production-Live-success)](https://socialcompass.ru)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://docker.com)

---

## 1. Назначение решения

Сервис **SocialCompass** решает проблему сложного и разрозненного поиска льгот, акций и доступных досуговых мест для социальных категорий граждан (студенты, пенсионеры, участники СВО).
Решение реализовано как чат-бот в **MAX Messenger**, интегрированный с единым веб-приложением (**MiniApp**), предоставляющим интерактивную карту, списки мест, личное избранное и ИИ-гида по акциям.

---

## 2. Основной пользовательский сценарий

1. **Онбординг**: Пользователь открывает чат-бот в MAX Messenger или запустив MiniApp. Проходит 2 быстрых шага: выбор города (Москва, Санкт-Петербург, Новосибирск) и льготной категории (Студенты, Пенсионеры, Участники СВО).
2. **Просмотр каталога**: Пользователь попадает на главный экран со списком мест и акций, отфильтрованных под его профиль. Доступно переключение между режимами «Список» и «Яндекс Карта».
3. **Фильтрация и детали**: Фильтрация по типам площадок (Музеи, Театры, Аквапарки, Боулинг, Котокафе, Спорт). Клик по карточке открывает подробный экран с адресом, графиком работы, информацией о скидке и кнопкой перехода.
4. **Избранное**: Добавление понравившихся мест в личное избранное с изолированным хранением на сервере.
5. **ИИ-Гид (AI Tunnel)**: Пользователь задаёт вопросы ассистенту в чате (например, *«Куда сходить со студенческим в субботу?»*). ИИ отвечает с учётом реальных мест из базы данных. При попытке задать посторонний вопрос (код, математика) ИИ вежливо напоминает о специализации сервиса.
6. **Синхронизация профиля**: При смене города или категории в MiniApp профиль мгновенно обновляется в БД и FSM-контексте чат-бота без повторного прохождения онбординга.

---

## 3. Состав и архитектура решения

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

## 4. Зависимости и требования

- **Python**: `3.11+`
- **Node.js**: `18+` (для сборки фронтенда miniapp)
- **Docker & Docker Compose**: Compose v2+
- **Зафиксированные версии зависимостей**: [`requirements.txt`](requirements.txt) (FastAPI 0.115.0, Uvicorn 0.32.0, Pydantic 2.10.0, HTTPX 0.28.1, aiomysql 0.2.0, Redis 5.2.0, Alembic 1.14.0).

---

## 5. Переменные окружения и используемые порты

### Используемые порты:
- `8000`: FastAPI Backend API & MiniApp Web Server
- `3306` / `3307`: MySQL Database
- `6379`: Redis Cache / FSM

### Файл переменных окружения `.env.example`:

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

## 6. Внешние сервисы и интеграции

1. **MAX Messenger Platform API** (`https://platform-api2.max.ru`): Получение обновлений пользователя, отправка кнопок и сообщений чат-бота.
2. **AI Tunnel API** (`https://api.aitunnel.ru/v1`): LLM-интеграция для генерации ответов ИИ-гида.
3. **Яндекс Карты API** (`https://api-maps.yandex.ru/2.1/`): Отображение интерактивных геолокационных меток мест на карте.

---

## 7. Описание работы с данными и порядок загрузки

Данные о скидках и партнерских площадках хранятся в MySQL в таблице `places`.
Базовый каталог поставляется в виде файла Excel в каталоге `data/`.

Порядок первичной загрузки данных в базу:
```bash
docker exec socialcompas_app python scripts/import_excel.py
```
Скрипт импортирует 87 записей проверенных мест и акций по г. Москва, Санкт-Петербург и Новосибирск.

---

## 8. 🚀 Быстрый запуск всех компонентов через Docker (1 команда)

### Шаг 1. Скопировать конфигурацию
```bash
cp .env.example .env
```

### Шаг 2. Запустить весь стек одной командой
```bash
docker compose up -d --build
```
*Сборка занимает не более 1-2 минут.*

### Шаг 3. Загрузить начальные данные мест
```bash
docker exec socialcompas_app python scripts/import_excel.py
```

После запуска доступно:
- **MiniApp (SPA)**: `http://localhost:8000`
- **Swagger UI (Интерактивная документация)**: `http://localhost:8000/docs`
- **OpenAPI 3.0 Спецификация**: `http://localhost:8000/openapi.json`
- **Проверка здоровья (Healthcheck)**: `http://localhost:8000/api/v1/cities`

---

## 9. Порядок остановки и повторного запуска решения

### Остановка решения:
```bash
docker compose down
```

### Повторный запуск решения:
```bash
docker compose up -d
```

### Полный перезапуск с очисткой контейнеров:
```bash
docker compose down -v && docker compose up -d --build
```

---

## 10. 🧪 Пошаговый сценарий проверки и примеры ожидаемого поведения

### Автоматическая проверка (Тест-сюит):
Выполните команду в терминале:
```bash
python test_bot.py
```

### Результат прохождения автоматической проверки:
```text
=======================================================
[SUITE 1] Bot FSM Onboarding & Navigation Flow → ALL OK
[SUITE 2] API Security & JWT Token Enforcement → ALL OK
[SUITE 3] Profile Sync Bot ↔ MiniApp → ALL OK
[SUITE 4] Places Catalog & Filtering → ALL OK
[SUITE 5] Favorites: User Isolation → ALL OK
[SUITE 6] AI Chat Assistant → ALL OK
=======================================================
✅ ALL TESTS PASSED SUCCESSFULLY!
```

### Ручная проверка через HTTP API:

1. **GET `/api/v1/cities`**
   - *Запрос*: `curl http://localhost:8000/api/v1/cities`
   - *Ожидаемый ответ* (`200 OK`): `{"ok": true, "count": 3, "items": [{"id": 1, "name": "Москва", "is_active": 1}, ...]}`

2. **GET `/api/v1/places?city=Москва&category=Студенты`**
   - *Запрос*: `curl "http://localhost:8000/api/v1/places?city=Москва&category=Студенты"`
   - *Ожидаемый ответ* (`200 OK`): `{"ok": true, "count": 5, "items": [{"id": 1, "title": "Третьяковская галерея", ...}]}`

3. **POST `/api/v1/chat` (ИИ-гид)**
   - *Запрос*: `curl -X POST http://localhost:8000/api/v1/chat -H "Content-Type: application/json" -d '{"messages": [{"role": "user", "content": "Какие музеи со скидкой?"}], "city": "Москва", "category": "Студенты"}'`
   - *Ожидаемый ответ* (`200 OK`): `{"ok": true, "message": "В Москве по студенческому билету вы можете посетить..."}`

4. **POST `/api/v1/chat` (Запрос вне темы — Guardrail)**
   - *Запрос*: `curl -X POST http://localhost:8000/api/v1/chat -H "Content-Type: application/json" -d '{"messages": [{"role": "user", "content": "Напиши код на Python"}], "city": "Москва", "category": "Студенты"}'`
   - *Ожидаемый ответ* (`200 OK`): `{"ok": true, "message": "Я — ассистент SocialCompass 🧭 и специализируюсь на поиске мест для отдыха и скидок..."}`

---

## 11. 🔑 Порядок работы с тестовыми данными и аккаунтами

Тестовые аккаунты зафиксированы в файле [`data/test_accounts.json`](data/test_accounts.json):

| Имя пользователя | Роль | `user_id` | Тестовый город | Категория |
|------------------|------|-----------|----------------|-----------|
| Алексей Иванов | Студент | `998877` | Москва | Студенты |
| Мария Петрова | Пенсионер | `554433` | Санкт-Петербург | Пенсионеры |
| Сергей Сидоров | Участник СВО | `112233` | Новосибирск | Участники СВО |

---

## 12. ⚠️ Известные ограничения

1. **Swagger UI на Production**: В целях безопасности документация Swagger (`/docs`) **отключена на боевом сервере** (`ENABLE_DOCS=false`). На локальном Docker-стеке она включена (`ENABLE_DOCS=true`).
2. **Лимит ИИ-запросов**: Во избежание абуза и превышения токенов установлен лимит 10 запросов в минуту на IP (`CHAT_RATE_LIMIT_PER_MINUTE=10`).
3. **География MVP**: Каталог мест покрывает 3 крупных города (Москва, Санкт-Петербург, Новосибирск) с возможностью быстрого расширения списка в `cities`.

---

## 📄 Спецификации и ссылки

- **OpenAPI 3.0 REST Specification**: [`openapi.yaml`](openapi.yaml)
- **Data API Schema Specification**: [`DATA-API.yaml`](DATA-API.yaml)
- **Тестовые аккаунты**: [`data/test_accounts.json`](data/test_accounts.json)
- **Тестовые данные мест**: [`data/test_data.json`](data/test_data.json)
- **Production Сайт (MiniApp SPA)**: [https://socialcompass.ru](https://socialcompass.ru)
- **Production API**: [https://api.socialcompass.ru](https://api.socialcompass.ru)
