import asyncio
import sys

# Force UTF-8 stdout encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from transport import MaxBotTransport, parse_update, MessageEvent, CallbackEvent
from fsm import MemoryStorage, FSMContext, SocialCompasSG
from handlers import Dispatcher


async def run_tests():
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

    print("\n[SUCCESS] ALL MIRO SCENARIO TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(run_tests())
