import asyncio
import argparse
import logging
import sys
from fastapi import FastAPI, Request
import uvicorn

import config
from transport import MaxBotTransport
from storage import init_db, get_db_pool, get_redis
from fsm import RedisFSMStorage, MySQLFSMStorage, MemoryStorage
from handlers import Dispatcher
from simulator import start_web_simulator, run_cli_simulator

logger = logging.getLogger("main")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(title="MAX Bot Webhook Receiver - SocialCompas Layered Architecture")
transport = MaxBotTransport()


async def setup_fsm_storage():
    """Initializes FSM storage engine (Redis > MySQL > Memory)."""
    try:
        redis_client = await get_redis()
        logger.info("Using RedisFSMStorage for FSM state management.")
        return RedisFSMStorage(redis_client)
    except Exception as exc:
        logger.warning(f"Redis unavailable ({exc}). Trying MySQL...")

    try:
        await init_db()
        from storage.db import get_db_pool
        pool = await get_db_pool()
        if pool:
            logger.info("Using MySQLFSMStorage for FSM state management.")
            return MySQLFSMStorage(pool)
    except Exception as exc:
        logger.warning(f"MySQL unavailable ({exc}). Using MemoryStorage.")

    logger.info("Using MemoryStorage as fallback.")
    return MemoryStorage()


async def start_long_polling(dp: Dispatcher):
    """
    Long-polling update listener for MAX Messenger API v2.
    """
    logger.info("🚀 Очистка активных Webhook-подписок перед запуском Long-Polling...")
    await transport.delete_subscriptions()

    logger.info("🚀 Запуск MAX Bot в режиме Long-Polling (platform-api2.max.ru)...")
    marker = None
    while True:
        try:
            updates_res = await transport.get_updates(marker=marker, timeout=25)
            if "updates" not in updates_res:
                logger.warning(f"Ответ API не содержит 'updates': {updates_res}")
                await asyncio.sleep(3)
                continue

            marker = updates_res.get("marker", marker)
            updates = updates_res.get("updates", [])
            for update in updates:
                logger.info(f"📩 Получено обновление: {update}")
                await dp.feed_update(update)
        except Exception as exc:
            logger.error(f"Polling loop exception: {exc}")
            await asyncio.sleep(3)


def main():
    parser = argparse.ArgumentParser(description="SocialCompas MAX Messenger Bot (Layered Architecture)")
    parser.add_argument("--sim", action="store_true", help="Запустить локальный веб-симулятор")
    parser.add_argument("--cli", action="store_true", help="Запустить интерактивный консольный симулятор")
    parser.add_argument("--polling", action="store_true", help="Запустить бот в режиме Long-Polling")
    parser.add_argument("--webhook", action="store_true", help="Запустить бот в режиме Webhook сервера")

    args = parser.parse_args()

    if args.cli:
        asyncio.run(run_cli_simulator())
    elif args.sim:
        start_web_simulator(host=config.HOST, port=config.PORT)
    else:
        async def run_bot():
            storage = await setup_fsm_storage()
            dp = Dispatcher(transport=transport, storage=storage)

            if args.webhook:
                logger.info(f"Запуск Webhook сервера на {config.HOST}:{config.PORT}")

                @app.post("/webhook")
                async def webhook_handler(request: Request):
                    update = await request.json()
                    await dp.feed_update(update)
                    return {"ok": True}

                config_uvicorn = uvicorn.Config(app, host=config.HOST, port=config.PORT)
                server = uvicorn.Server(config_uvicorn)
                await server.serve()
            else:
                await start_long_polling(dp)

        asyncio.run(run_bot())


if __name__ == "__main__":
    main()
