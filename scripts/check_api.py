"""End-to-end проверка контракта API (в т.ч. авторизации) против запущенного стенда.

    python scripts/check_api.py                       # локальный Docker (http://localhost:8000)
    BASE_URL=https://api.socialcompass.ru MAX_BOT_TOKEN=... python scripts/check_api.py

Подписывает initData токеном бота (как это делает MAX), получает токены двух тестовых пользователей и
проверяет: каталог, авторизацию, изоляцию данных пользователей (401/403), избранное, профиль.
Токен бота нужен только для подписи; в репозитории он не хранится.
"""
import hashlib
import hmac
import json
import os
import sys
import time
from urllib.parse import urlencode

import httpx

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
BOT_TOKEN = os.getenv("MAX_BOT_TOKEN", "")
API = f"{BASE}/api/v1"
failed = 0


def check(name: str, cond: bool, extra: str = ""):
    global failed
    print(f"[{'OK' if cond else 'FAIL'}] {name} {extra}")
    if not cond:
        failed += 1


def init_data(user_id: int) -> str:
    fields = {"auth_date": str(int(time.time())), "user": json.dumps({"id": user_id, "first_name": "Test"}, separators=(",", ":"))}
    dcs = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


def main():
    if not BOT_TOKEN:
        sys.exit("Задайте MAX_BOT_TOKEN (нужен только для подписи тестового initData)")
    c = httpx.Client(timeout=20.0)

    r = c.get(f"{API}/cities")
    check("GET /cities → 200", r.status_code == 200 and r.json().get("count", 0) >= 3)
    r = c.get(f"{API}/places", params={"city": "Москва", "category": "Студенты"})
    items = r.json().get("items", [])
    check("GET /places?city&category → 200 с местами", r.status_code == 200 and len(items) > 0, f"({len(items)} мест)")
    check("места содержат points (координаты меток)", all(isinstance(p.get("points"), list) for p in items))
    place_id = items[0]["id"] if items else None
    if place_id:
        check("GET /places/{id} → 200", c.get(f"{API}/places/{place_id}").status_code == 200)
    check("GET /places/999999 → 404", c.get(f"{API}/places/999999").status_code == 404)

    check("POST /auth/webapp с поддельной подписью → 401",
          c.post(f"{API}/auth/webapp", json={"init_data": "auth_date=1&user=%7B%22id%22%3A1%7D&hash=bad"}).status_code == 401)
    tokens = {}
    for uid in (998877, 554433):
        r = c.post(f"{API}/auth/webapp", json={"init_data": init_data(uid)})
        check(f"POST /auth/webapp (user {uid}) → 200 + token", r.status_code == 200 and "token" in r.json())
        tokens[uid] = {"Authorization": f"Bearer {r.json().get('token', '')}"}
    a, b = tokens[998877], tokens[554433]

    check("GET /favorites без токена → 401", c.get(f"{API}/favorites").status_code == 401)
    check("GET /profile/998877 без токена → 401", c.get(f"{API}/profile/998877").status_code == 401)
    check("GET /profile/998877 чужим токеном → 403", c.get(f"{API}/profile/998877", headers=b).status_code == 403)
    check("GET /favorites/998877 чужим токеном → 403", c.get(f"{API}/favorites/998877", headers=b).status_code == 403)

    body = {"user_id": "998877", "city": "Санкт-Петербург", "category": "Пенсионеры"}
    check("POST /profile своим токеном → 200", c.post(f"{API}/profile", json=body, headers=a).status_code == 200)
    check("POST /profile без токена → 401", c.post(f"{API}/profile", json=body).status_code == 401)
    p = c.get(f"{API}/profile/998877", headers=a).json().get("profile") or {}
    check("профиль сохранился", p.get("city") == "Санкт-Петербург" and p.get("category") == "Пенсионеры", str(p))
    c.post(f"{API}/profile", json={**body, "city": "Москва", "category": "Студенты"}, headers=a)
    check("профиль нового пользователя → null (запустится опрос)", c.get(f"{API}/profile/guest_nobody").json().get("profile") is None)

    if place_id:
        check("POST /favorites/{uid}/{place} → 200", c.post(f"{API}/favorites/998877/{place_id}", headers=a).status_code == 200)
        ids = [x["id"] for x in c.get(f"{API}/favorites/998877", headers=a).json().get("items", [])]
        check("место в избранном владельца", place_id in ids)
        ids_b = [x["id"] for x in c.get(f"{API}/favorites/554433", headers=b).json().get("items", [])]
        check("у другого пользователя его нет (изоляция)", place_id not in ids_b)
        check("DELETE чужим токеном → 403", c.delete(f"{API}/favorites/998877/{place_id}", headers=b).status_code == 403)
        check("POST /favorites/{place} (по токену) → 200", c.post(f"{API}/favorites/{place_id}", headers=a).status_code == 200)
        check("DELETE /favorites/{place} (по токену) → 200", c.delete(f"{API}/favorites/{place_id}", headers=a).status_code == 200)
        check("DELETE своим токеном → 200", c.delete(f"{API}/favorites/998877/{place_id}", headers=a).status_code == 200)

    r = c.post(f"{API}/chat", json={"messages": [{"role": "user", "content": "Какие музеи со скидкой есть в Москве?"}],
                                    "city": "Москва", "category": "Студенты"})
    check("POST /chat → 200", r.status_code == 200 and bool(r.json().get("message")))

    print(f"\n{'✅ Все проверки пройдены' if not failed else f'❌ Провалено проверок: {failed}'}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
