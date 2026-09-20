import logging
import redis.asyncio as aioredis
from typing import Optional

import config

logger = logging.getLogger("storage.redis")
_redis_pool: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """
    Returns an async Redis client instance using connection pool.
    """
    global _redis_pool
    if _redis_pool is None:
        try:
            _redis_pool = aioredis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                password=config.REDIS_PASSWORD,
                decode_responses=True,
            )
            await _redis_pool.ping()
            logger.info("Connected to Redis successfully.")
        except Exception as exc:
            logger.warning(f"Failed to connect to Redis: {exc}. Using fallback in-memory store.")
            _redis_pool = None
            raise exc

    return _redis_pool
