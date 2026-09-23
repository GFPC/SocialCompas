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


async def run_bot_tests():
    print("[TEST] Testing Miro Scenario Flow...")

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

    # 1. Start command -> Select City
    await dp.feed_update({"update_type": "message_created", "chat_id": "u1", "message": {"body": {"text": "/start"}, "sender": {"user_id": "u1"}}})
    assert len(dummy.sent) == 1
    assert "Выберите ваш город" in dummy.sent[0][1]
    print("[OK] Step 1: Onboarding / City Selection test passed")

    # 2. Select City -> Select Category
    await dp.feed_update({"update_type": "message_callback", "callback": {"callback_id": "c1", "payload": "city_Москва", "user": {"user_id": "u1"}}, "message": {"recipient": {"chat_id": "u1"}}})
    assert len(dummy.sent) == 2
    assert "Теперь выберите вашу категорию" in dummy.sent[1][1]
    print("[OK] Step 2: City Selection -> Category Selection test passed")

    # 3. Select Category -> Onboarding Complete & Main Menu
    await dp.feed_update({"update_type": "message_callback", "callback": {"callback_id": "c2", "payload": "cat_Студент", "user": {"user_id": "u1"}}, "message": {"recipient": {"chat_id": "u1"}}})
    assert len(dummy.sent) == 3
    assert "Благодарю за ответы" in dummy.sent[2][1]
    print("[OK] Step 3: Category Selection -> Main Menu test passed")

    # 4. View Settings
    await dp.feed_update({"update_type": "message_callback", "callback": {"callback_id": "c3", "payload": "view_settings", "user": {"user_id": "u1"}}, "message": {"recipient": {"chat_id": "u1"}}})
    assert len(dummy.sent) == 4
    assert "Настройки профиля" in dummy.sent[3][1]
    print("[OK] Step 4: Settings View test passed")


def run_api_tests():
    print("\n[TEST] Testing API Endpoints & Security Token Auth...")
    client = TestClient(app)

    # 1. GET /api/v1/cities
    res = client.get("/api/v1/cities")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["ok"] is True
    assert len(data["items"]) >= 3
    print("[OK] API Step 1: GET /api/v1/cities passed")

    # 2. GET /api/v1/categories
    res = client.get("/api/v1/categories")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["ok"] is True
    assert len(data["items"]) >= 3
    print("[OK] API Step 2: GET /api/v1/categories passed")

    # 3. POST /api/v1/auth/token
    res = client.post("/api/v1/auth/token", json={"user_id": "user_test_123"})
    assert res.status_code == 200, res.text
    token = res.json().get("token")
    assert token is not None
    print("[OK] API Step 3: Token Generation POST /api/v1/auth/token passed")

    # 4. GET /api/v1/favorites without token -> 401 Unauthorized
    res = client.get("/api/v1/favorites")
    assert res.status_code == 401
    print("[OK] API Step 4: Protected route GET /api/v1/favorites without token correctly rejected (401)")

    # 5. GET /api/v1/favorites with Bearer Token -> 200 OK
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/api/v1/favorites", headers=headers)
    assert res.status_code == 200, res.text
    print("[OK] API Step 5: Protected route GET /api/v1/favorites with valid Bearer Token passed (200)")

    # 6. GET /api/v1/profile/me with Bearer Token -> 200 OK
    res = client.get("/api/v1/profile/me", headers=headers)
    assert res.status_code == 200, res.text
    print("[OK] API Step 6: Protected route GET /api/v1/profile/me passed (200)")

    # 7. WebApp initData HMAC verification
    user_json = json.dumps({"id": 998877, "first_name": "SecureUser"}, separators=(',', ':'))
    auth_date = str(int(time.time()))
    data_dict = {"auth_date": auth_date, "user": user_json}
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data_dict.items()))
    secret_key = hmac.new(b"WebAppData", config.MAX_BOT_TOKEN.encode('utf-8'), hashlib.sha256).digest()
    hash_val = hmac.new(secret_key, data_check_string.encode('utf-8'), hashlib.sha256).hexdigest()
    data_dict["hash"] = hash_val
    valid_init_data = urlencode(data_dict)

    res = client.post("/api/v1/auth/webapp", json={"init_data": valid_init_data})
    assert res.status_code == 200, res.text
    assert res.json()["user_id"] == "998877"
    print("[OK] API Step 7: WebApp initData HMAC verification passed (200 OK)")

    # Tampered initData -> 401 Unauthorized
    tampered_init_data = valid_init_data.replace("998877", "111111")
    res = client.post("/api/v1/auth/webapp", json={"init_data": tampered_init_data})
    assert res.status_code == 401
    print("[OK] API Step 8: Tampered initData correctly rejected with 401 Unauthorized")


if __name__ == "__main__":
    asyncio.run(run_bot_tests())
    run_api_tests()
    print("\n[SUCCESS] ALL BOT AND API SECURITY TESTS PASSED SUCCESSFULLY!")
