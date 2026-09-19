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
    logger.info("🚀 Запуск MAX Bot в режиме Long-Polling (platform-api2.max.ru)...")
    offset = 0
    while True:
        try:
            updates_res = await api.get_updates(offset=offset, timeout=20)
            if not updates_res.get("ok", True) and "error_code" in updates_res:
                logger.warning(f"Ошибка получения обновлений: {updates_res}")
                await asyncio.sleep(5)
                continue

            updates = updates_res.get("result", [])
            for update in updates:
                offset = max(offset, update.get("update_id", 0) + 1)
                chat_id, response_text, keyboard = await handlers.handle_update(update)
                if chat_id and response_text:
                    await api.send_message(chat_id=chat_id, text=response_text, reply_markup=keyboard)
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
    elif args.sim or (config.SIMULATION_MODE and not args.polling and not args.webhook):
        start_web_simulator(host=config.HOST, port=config.PORT)
    elif args.polling:
        asyncio.run(start_long_polling())
    elif args.webhook:
        logger.info(f"Запуск Webhook сервера на {config.HOST}:{config.PORT}")
        uvicorn.run(app, host=config.HOST, port=config.PORT)
    else:
        # Default fallback to web simulator if token is placeholder
        if config.MAX_BOT_TOKEN == "your_max_bot_token_here" or config.SIMULATION_MODE:
            logger.info("Токен бота не задан или взведен SIMULATION_MODE. Запуск локального симулятора...")
            start_web_simulator(host=config.HOST, port=config.PORT)
        else:
            asyncio.run(start_long_polling())


if __name__ == "__main__":
    main()
