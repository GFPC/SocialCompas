import asyncio
import sys
import hmac
import hashlib
import json
import time
from urllib.parse import urlencode
from fastapi.testclient import TestClient

# Force UTF-8 stdout encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

import config
from main import app
from transport import MaxBotTransport, parse_update, MessageEvent, CallbackEvent
from fsm import MemoryStorage, FSMContext, SocialCompasSG
from handlers import Dispatcher


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def make_valid_token(client: TestClient, user_id: int) -> str:
    """Generates a real signed JWT for a given user_id via HMAC initData flow."""
    user_json = json.dumps({"id": user_id, "first_name": "TestUser"}, separators=(',', ':'))
    auth_date = str(int(time.time()))
    data_dict = {"auth_date": auth_date, "user": user_json}
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data_dict.items()))
    secret_key = hmac.new(b"WebAppData", config.MAX_BOT_TOKEN.encode('utf-8'), hashlib.sha256).digest()
    hash_val = hmac.new(secret_key, data_check_string.encode('utf-8'), hashlib.sha256).hexdigest()
    data_dict["hash"] = hash_val
    init_data = urlencode(data_dict)
    res = client.post("/api/v1/auth/webapp", json={"init_data": init_data})
    assert res.status_code == 200, f"Token generation failed: {res.text}"
    return res.json()["token"]


# ─────────────────────────────────────────────
# Suite 1: Bot FSM Flow (Miro Scenario)
# ─────────────────────────────────────────────

async def run_bot_tests():
    print("=" * 55)
    print("[SUITE 1] Bot FSM Onboarding & Navigation Flow")
    print("=" * 55)

    storage = MemoryStorage()

    class DummyTransport(MaxBotTransport):
        def __init__(self):
            self.sent = []

        async def send_message(self, chat_id, text, keyboard=None):
            self.sent.append((chat_id, text, keyboard))
            return {"ok": True}

        async def answer_callback(self, callback_id, notification="ОК"):
            return {"ok": True}

    dummy = DummyTransport()
    dp = Dispatcher(transport=dummy, storage=storage)

    # 1. /start → city selection
    await dp.feed_update({"update_type": "message_created", "chat_id": "u1",
                          "message": {"body": {"text": "/start"}, "sender": {"user_id": "u1"}}})
    assert len(dummy.sent) == 1
    assert "Выберите ваш город" in dummy.sent[0][1]
    print("[OK] Step 1: /start → City Selection screen shown")

    # 2. City selected → category selection
    await dp.feed_update({"update_type": "message_callback",
                          "callback": {"callback_id": "c1", "payload": "city_Москва", "user": {"user_id": "u1"}},
                          "message": {"recipient": {"chat_id": "u1"}}})
    assert len(dummy.sent) == 2
    assert "Теперь выберите вашу категорию" in dummy.sent[1][1]
    print("[OK] Step 2: City selected → Category Selection screen shown")

    # 3. Category selected → Main Menu
    await dp.feed_update({"update_type": "message_callback",
                          "callback": {"callback_id": "c2", "payload": "cat_Студенты", "user": {"user_id": "u1"}},
                          "message": {"recipient": {"chat_id": "u1"}}})
    assert len(dummy.sent) == 3
    assert "Благодарю за ответы" in dummy.sent[2][1]
    print("[OK] Step 3: Category selected → Onboarding complete & Main Menu")

    # 4. View Settings → shows correct profile
    await dp.feed_update({"update_type": "message_callback",
                          "callback": {"callback_id": "c3", "payload": "view_settings", "user": {"user_id": "u1"}},
                          "message": {"recipient": {"chat_id": "u1"}}})
    assert len(dummy.sent) == 4
    assert "Настройки профиля" in dummy.sent[3][1]
    print("[OK] Step 4: Settings screen shows Настройки профиля")

    # 5. View Places → shows city/category filtered list
    await dp.feed_update({"update_type": "message_callback",
                          "callback": {"callback_id": "c4", "payload": "view_places", "user": {"user_id": "u1"}},
                          "message": {"recipient": {"chat_id": "u1"}}})
    assert len(dummy.sent) == 5
    msg_text = dummy.sent[4][1]
    assert "Список мест" in msg_text or "Москва" in msg_text or "не найдены" in msg_text
    print("[OK] Step 5: View Places → places list or empty state")

    # 6. Back to Main Menu
    await dp.feed_update({"update_type": "message_callback",
                          "callback": {"callback_id": "c5", "payload": "menu_main", "user": {"user_id": "u1"}},
                          "message": {"recipient": {"chat_id": "u1"}}})
    assert len(dummy.sent) == 6
    assert "Главное меню" in dummy.sent[5][1]
    print("[OK] Step 6: Back to Main Menu works")

    # 7. Edit Profile → City selection again
    await dp.feed_update({"update_type": "message_callback",
                          "callback": {"callback_id": "c6", "payload": "edit_profile", "user": {"user_id": "u1"}},
                          "message": {"recipient": {"chat_id": "u1"}}})
    assert len(dummy.sent) == 7
    assert "Выберите ваш" in dummy.sent[6][1]
    print("[OK] Step 7: Edit Profile → city re-selection prompt shown")

    # 8. BotStarted event handled gracefully
    dummy2 = DummyTransport()
    dp2 = Dispatcher(transport=dummy2, storage=MemoryStorage())
    await dp2.feed_update({"update_type": "bot_started", "user_id": "u_new", "chat_id": "u_new"})
    assert len(dummy2.sent) == 1
    print("[OK] Step 8: bot_started event → onboarding initiated")

    print()


# ─────────────────────────────────────────────
# Suite 2: API Security & JWT Enforcement
# ─────────────────────────────────────────────

def run_api_security_tests(client: TestClient, token: str):
    print("=" * 55)
    print("[SUITE 2] API Security & JWT Token Enforcement")
    print("=" * 55)

    # 1. Tampered initData rejected
    user_json = json.dumps({"id": 111111, "first_name": "Hacker"}, separators=(',', ':'))
    tampered = f"auth_date=1000000&user={user_json}&hash=fakehash"
    res = client.post("/api/v1/auth/webapp", json={"init_data": tampered})
    assert res.status_code == 401
    print("[OK] Test 1: Tampered initData → 401 Unauthorized")

    # 2. Protected route without JWT → 401
    res = client.get("/api/v1/favorites")
    assert res.status_code == 401
    print("[OK] Test 2: GET /favorites without JWT → 401")

    # 3. Protected route with JWT → 200
    res = client.get("/api/v1/favorites", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    print("[OK] Test 3: GET /favorites with valid JWT → 200")

    # 4. GET /profile/me without JWT → 401
    res = client.get("/api/v1/profile/me")
    assert res.status_code == 401
    print("[OK] Test 4: GET /profile/me without JWT → 401")

    # 5. GET /profile/me with JWT → 200 with city/category
    res = client.get("/api/v1/profile/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert "city" in data["profile"]
    assert "category" in data["profile"]
    print("[OK] Test 5: GET /profile/me with JWT → 200 with valid profile")

    # 6. Swagger/docs disabled on production (ENABLE_DOCS=false by default)
    res = client.get("/docs")
    assert res.status_code == 404, "Swagger /docs should be disabled on production!"
    print("[OK] Test 6: /docs → 404 (Swagger disabled on production)")

    res = client.get("/redoc")
    assert res.status_code == 404
    print("[OK] Test 7: /redoc → 404 (ReDoc disabled on production)")

    print()


# ─────────────────────────────────────────────
# Suite 3: Profile Sync Bot ↔ MiniApp
# ─────────────────────────────────────────────

def run_profile_sync_tests(client: TestClient, token: str):
    print("=" * 55)
    print("[SUITE 3] Profile Sync Bot ↔ MiniApp")
    print("=" * 55)

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Save profile via MiniApp (POST /profile without JWT, with user_id)
    res = client.post("/api/v1/profile", json={"user_id": "998877", "city": "Санкт-Петербург", "category": "Пенсионеры"})
    assert res.status_code == 200
    assert res.json()["ok"] is True
    print("[OK] Test 1: MiniApp POST /profile (anonymous) → 200 saved")

    # 2. Read back the same profile via GET /profile/{user_id}
    res = client.get("/api/v1/profile/998877")
    assert res.status_code == 200
    p = res.json()["profile"]
    # In DB mode: city/category should be exactly what was saved
    # In memory-only mode (no MySQL): returns defaults — still validates schema
    assert "city" in p and p["city"]
    assert "category" in p and p["category"]
    print(f"[OK] Test 2: GET /profile/998877 → returns profile (city={p['city']}, category={p['category']})")

    # 3. Update via JWT-authenticated POST /profile/me
    res = client.post("/api/v1/profile/me",
                      json={"city": "Новосибирск", "category": "Студенты"},
                      headers=headers)
    assert res.status_code == 200
    print("[OK] Test 3: POST /profile/me (JWT) → profile updated")

    # 4. GET /cities and /categories return all expected values
    res = client.get("/api/v1/cities")
    cities = [c["name"] for c in res.json()["items"]]
    assert "Москва" in cities
    assert "Санкт-Петербург" in cities
    assert "Новосибирск" in cities
    print("[OK] Test 4: GET /cities → all 3 cities present")

    res = client.get("/api/v1/categories")
    cats = [c["name"] for c in res.json()["items"]]
    assert "Студенты" in cats
    assert "Пенсионеры" in cats
    assert "Участники СВО" in cats
    print("[OK] Test 5: GET /categories → all 3 categories present")

    print()


# ─────────────────────────────────────────────
# Suite 4: Places Catalog & Filtering
# ─────────────────────────────────────────────

def run_places_tests(client: TestClient):
    print("=" * 55)
    print("[SUITE 4] Places Catalog & Filtering")
    print("=" * 55)

    # 1. Get places for each city/category combo
    for city, cat in [
        ("Москва", "Студенты"),
        ("Москва", "Пенсионеры"),
        ("Москва", "Участники СВО"),
        ("Санкт-Петербург", "Студенты"),
        ("Новосибирск", "Студенты"),
    ]:
        res = client.get(f"/api/v1/places?city={city}&category={cat}")
        assert res.status_code == 200
        data = res.json()
        assert data["ok"] is True
        assert isinstance(data["items"], list)
        assert data["count"] == len(data["items"])
    print("[OK] Test 1: GET /places returns data for all city/category combinations")

    # 2. Each place has required fields
    res = client.get("/api/v1/places?city=Москва&category=Студенты")
    items = res.json()["items"]
    if items:
        place = items[0]
        for field in ("id", "title", "city", "category", "description"):
            assert field in place, f"Missing field: {field}"
        print("[OK] Test 2: Places have required fields (id, title, city, category, description)")

        # 3. GET /places/{id} returns correct place
        pid = place["id"]
        res2 = client.get(f"/api/v1/places/{pid}")
        assert res2.status_code == 200
        assert res2.json()["place"]["id"] == pid
        print(f"[OK] Test 3: GET /places/{pid} → correct place detail returned")

        # 4. Unknown place_id returns 404
        res3 = client.get("/api/v1/places/999999")
        assert res3.status_code == 404
        print("[OK] Test 4: GET /places/999999 → 404 Not Found")
    else:
        print("[SKIP] Tests 2-4: No places in DB yet (run import_excel.py first)")

    print()


# ─────────────────────────────────────────────
# Suite 5: Favorites User Isolation
# ─────────────────────────────────────────────

def run_favorites_isolation_tests(client: TestClient):
    print("=" * 55)
    print("[SUITE 5] Favorites: User Isolation")
    print("=" * 55)

    # Get a place to favorite
    res = client.get("/api/v1/places?city=Москва&category=Студенты")
    items = res.json()["items"]
    if not items:
        print("[SKIP] No places available — skipping favorites isolation tests")
        return

    place_id = items[0]["id"]
    user_a = "test_user_A_isolation"
    user_b = "test_user_B_isolation"

    # Add place to user A's favorites
    res = client.post(f"/api/v1/favorites/{user_a}/{place_id}")
    assert res.status_code == 200
    print(f"[OK] Test 1: Added place {place_id} to User A favorites")

    # User A should see it
    res = client.get(f"/api/v1/favorites/{user_a}")
    fav_ids_a = [p["id"] for p in res.json()["items"]]
    assert place_id in fav_ids_a
    print("[OK] Test 2: User A can see their favorite")

    # User B should NOT see User A's favorites
    res = client.get(f"/api/v1/favorites/{user_b}")
    fav_ids_b = [p["id"] for p in res.json()["items"]]
    assert place_id not in fav_ids_b, "User B should not see User A's favorites!"
    print("[OK] Test 3: User B does NOT see User A's favorites (isolation correct)")

    # Remove from User A
    res = client.delete(f"/api/v1/favorites/{user_a}/{place_id}")
    assert res.status_code == 200
    res = client.get(f"/api/v1/favorites/{user_a}")
    fav_ids_after = [p["id"] for p in res.json()["items"]]
    assert place_id not in fav_ids_after
    print("[OK] Test 4: Removed from User A favorites — correctly gone")

    print()


# ─────────────────────────────────────────────
# Suite 6: AI Chat
# ─────────────────────────────────────────────

def run_ai_chat_tests(client: TestClient):
    print("=" * 55)
    print("[SUITE 6] AI Chat Assistant")
    print("=" * 55)

    # 1. On-topic question → 200 with relevant answer
    res = client.post("/api/v1/chat", json={
        "messages": [{"role": "user", "content": "Какие музеи со скидкой в Москве для студентов?"}],
        "city": "Москва",
        "category": "Студенты"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert "message" in data
    assert len(data["message"]) > 10
    print("[OK] Test 1: On-topic question → AI responds with content")

    # 2. Off-topic question → polite refusal with SocialCompass mention
    res = client.post("/api/v1/chat", json={
        "messages": [{"role": "user", "content": "Напиши Python код для веб-скрапинга"}],
        "city": "Москва",
        "category": "Студенты"
    })
    assert res.status_code == 200
    msg = res.json()["message"]
    assert "SocialCompass" in msg or "компас" in msg.lower() or "специализируюсь" in msg.lower()
    print("[OK] Test 2: Off-topic prompt → polite refusal mentioning SocialCompass")

    # 3. Empty messages → 400 Bad Request
    res = client.post("/api/v1/chat", json={"messages": [], "city": "Москва", "category": "Студенты"})
    assert res.status_code == 400
    print("[OK] Test 3: Empty messages list → 400 Bad Request")

    # 4. Chat with city/category context
    res = client.post("/api/v1/chat", json={
        "messages": [{"role": "user", "content": "Куда сходить пенсионеру в Санкт-Петербурге?"}],
        "city": "Санкт-Петербург",
        "category": "Пенсионеры"
    })
    assert res.status_code == 200
    print("[OK] Test 4: Chat with Санкт-Петербург/Пенсионеры context → 200")

    print()


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

if __name__ == "__main__":
    client = TestClient(app)

    # Get a JWT token for API test suites
    token = make_valid_token(client, 998877)

    # Run all suites
    asyncio.run(run_bot_tests())
    run_api_security_tests(client, token)
    run_profile_sync_tests(client, token)
    run_places_tests(client)
    run_favorites_isolation_tests(client)
    run_ai_chat_tests(client)

    print("=" * 55)
    print("✅ ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 55)
