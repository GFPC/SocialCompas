import asyncio
import argparse
import logging
import sys
from fastapi import FastAPI, Request
import uvicorn

import config
from max_api import MaxBotAPI
from handlers import BotHandlers
from simulator import start_web_simulator, run_cli_simulator

logger = logging.getLogger("main")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(title="MAX Bot Webhook Receiver - SocialCompas")
api = MaxBotAPI()
handlers = BotHandlers(api=api)


@app.post("/webhook")
async def webhook_handler(request: Request):
    """
    Webhook endpoint for receiving updates from MAX Messenger Platform.
    """
    try:
        update = await request.json()
        logger.info(f"Received webhook update: {update}")
        chat_id, response_text, keyboard = await handlers.handle_update(update)
        if chat_id and response_text:
            await api.send_message(chat_id=chat_id, text=response_text, reply_markup=keyboard)
        return {"ok": True}
    except Exception as exc:
        logger.error(f"Webhook processing error: {exc}", exc_info=True)
        return {"ok": False, "error": str(exc)}


async def start_long_polling():
    """
    Long-polling update listener for MAX Messenger API.
    """
    logger.info("🚀 Очистка активных Webhook-подписок перед запуском Long-Polling...")
    await api.delete_subscriptions()

    logger.info("🚀 Запуск MAX Bot в режиме Long-Polling (platform-api2.max.ru)...")
    marker = None
    while True:
        try:
            updates_res = await api.get_updates(marker=marker, timeout=25)
            if "updates" not in updates_res:
                logger.warning(f"Ответ API не содержит 'updates': {updates_res}")
                await asyncio.sleep(3)
                continue

            marker = updates_res.get("marker", marker)
            updates = updates_res.get("updates", [])
            for update in updates:
                logger.info(f"📩 Получено обновление: {update}")
                chat_id, response_text, keyboard = await handlers.handle_update(update)
                if chat_id and response_text:
                    logger.info(f"📤 Отправка ответа в chat_id {chat_id}: {response_text[:30]}...")
                    res = await api.send_message(chat_id=chat_id, text=response_text, reply_markup=keyboard)
                    logger.info(f"Статус отправки: {res}")
        except Exception as exc:
            logger.error(f"Polling loop exception: {exc}")
            await asyncio.sleep(3)


def main():
    parser = argparse.ArgumentParser(description="SocialCompas MAX Messenger Bot")
    parser.add_argument("--sim", action="store_true", help="Запустить локальный веб-симулятор")
    parser.add_argument("--cli", action="store_true", help="Запустить интерактивный консольный симулятор")
    parser.add_argument("--polling", action="store_true", help="Запустить бот в режиме Long-Polling")
    parser.add_argument("--webhook", action="store_true", help="Запустить бот в режиме Webhook сервера")

    args = parser.parse_args()

    if args.cli:
        asyncio.run(run_cli_simulator())
    elif args.sim:
        start_web_simulator(host=config.HOST, port=config.PORT)
    elif args.webhook:
        logger.info(f"Запуск Webhook сервера на {config.HOST}:{config.PORT}")
        uvicorn.run(app, host=config.HOST, port=config.PORT)
    else:
        # Default mode: Long-Polling on MAX API
        asyncio.run(start_long_polling())


if __name__ == "__main__":
    main()
