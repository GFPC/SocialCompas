import asyncio
import argparse
import logging
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import config
from transport import MaxBotTransport
from storage import init_db, get_db_pool, get_redis
from fsm import RedisFSMStorage, MySQLFSMStorage, MemoryStorage
from handlers import Dispatcher
from api import v1_router
from simulator import start_web_simulator, run_cli_simulator

logger = logging.getLogger("main")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="SocialCompas Unified Backend API & MAX Bot",
    version="2.0.0",
    description="Unified backend providing REST API for MiniApp and Webhook/Polling for MAX Messenger Bot."
)

# Enable CORS for MiniApp frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register MiniApp REST API Routers
app.include_router(v1_router)

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
    parser = argparse.ArgumentParser(description="SocialCompas MAX Messenger Bot & MiniApp Backend")
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
        async def run_bot_and_api():
            await init_db()
            storage = await setup_fsm_storage()
            dp = Dispatcher(transport=transport, storage=storage)

            @app.post("/webhook")
            async def webhook_handler(request: Request):
                update = await request.json()
                await dp.feed_update(update)
                return {"ok": True}

            if args.webhook:
                logger.info(f"Запуск Webhook сервера и REST API на http://{config.HOST}:{config.PORT}")
                config_uvicorn = uvicorn.Config(app, host=config.HOST, port=config.PORT)
                server = uvicorn.Server(config_uvicorn)
                await server.serve()
            else:
                # Run FastAPI REST API server alongside background Long-Polling loop
                logger.info(f"Запуск FastAPI REST API сервер на http://{config.HOST}:{config.PORT}")
                config_uvicorn = uvicorn.Config(app, host=config.HOST, port=config.PORT)
                server = uvicorn.Server(config_uvicorn)

                await asyncio.gather(
                    server.serve(),
                    start_long_polling(dp)
                )

        asyncio.run(run_bot_and_api())


if __name__ == "__main__":
    main()
