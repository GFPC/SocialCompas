import asyncio
import sys

# Force UTF-8 stdout encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from handlers import BotHandlers


async def run_tests():
    print("[TEST] Testing BotHandlers...")
    handlers = BotHandlers()

    # Test /start command
    chat_id, text, kb = await handlers.handle_update({"message": {"text": "/start", "chat": {"id": "test_1"}}})
    assert chat_id == "test_1"
    assert "Добро пожаловать" in text
    assert kb is not None
    print("[OK] /start command test passed")

    # Test /compass command
    chat_id, text, kb = await handlers.handle_update({"message": {"text": "/compass", "chat": {"id": "test_1"}}})
    assert "Социальный Компас" in text
    assert len(kb["inline_keyboard"]) >= 4
    print("[OK] /compass command test passed")

    # Test inline button callbacks
    callbacks = ["cat_support", "cat_events", "cat_legal", "cat_volunteer", "menu_main"]
    for cb in callbacks:
        chat_id, text, kb = await handlers.handle_update({"callback_query": {"data": cb, "message": {"chat": {"id": "test_1"}}}})
        assert text is not None
        assert kb is not None
        print(f"[OK] Callback button '{cb}' test passed")

    # Test /echo
    chat_id, text, _ = await handlers.handle_update({"message": {"text": "/echo Hello MAX", "chat": {"id": "test_1"}}})
    assert "Hello MAX" in text
    print("[OK] /echo command test passed")

    print("\n[SUCCESS] ALL BOT HANDLER TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(run_tests())
