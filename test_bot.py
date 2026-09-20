import asyncio
import sys

# Force UTF-8 stdout encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from transport import MaxBotTransport, parse_update, MessageEvent, CallbackEvent
from fsm import MemoryStorage, FSMContext, State, StatesGroup
from handlers import Dispatcher


class Form(StatesGroup):
    name = State("Form:name")
    age = State("Form:age")


async def run_tests():
    print("[TEST] Testing FSM & Transport Architecture...")

    # 1. Test Event Parsing
    raw_msg = {
        "update_type": "message_created",
        "chat_id": 12345,
        "message": {"body": {"text": "/start"}, "sender": {"user_id": 999}}
    }
    event = parse_update(raw_msg)
    assert isinstance(event, MessageEvent)
    assert event.text == "/start"
    print("[OK] Event Parsing test passed")

    # 2. Test FSM Context
    storage = MemoryStorage()
    ctx = FSMContext(storage, user_id="user_100")
    await ctx.set_state(Form.name)
    assert await ctx.get_state() == "Form:name"

    await ctx.update_data(name="Max")
    data = await ctx.get_data()
    assert data["name"] == "Max"
    print("[OK] FSM Context & Storage test passed")

    # 3. Test Dispatcher routing (Mock transport)
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

    # Feed message update
    await dp.feed_update(raw_msg)
    assert len(dummy.sent) == 1
    assert "Добро пожаловать" in dummy.sent[0][1]
    print("[OK] Dispatcher Message Routing test passed")

    # Feed callback update
    raw_cb = {
        "update_type": "message_callback",
        "callback": {"callback_id": "cb_1", "payload": "cat_support", "user": {"user_id": 999}},
        "message": {"recipient": {"chat_id": 12345}}
    }
    await dp.feed_update(raw_cb)
    assert len(dummy.sent) == 2
    assert "Социальные выплаты" in dummy.sent[1][1]
    print("[OK] Dispatcher Callback Routing test passed")

    print("\n[SUCCESS] ALL ARCHITECTURE & LAYER TESTS PASSED!")


if __name__ == "__main__":
    asyncio.run(run_tests())
