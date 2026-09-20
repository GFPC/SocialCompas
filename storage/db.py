import logging
import aiomysql
from typing import Optional

import config

logger = logging.getLogger("storage.db")
_db_pool: Optional[aiomysql.Pool] = None


async def init_db():
    """
    Initializes MySQL connection pool and creates required tables.
    """
    global _db_pool
    try:
        _db_pool = await aiomysql.create_pool(
            host=config.MYSQL_HOST,
            port=config.MYSQL_PORT,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            db=config.MYSQL_DB,
            autocommit=True,
            maxsize=10,
        )
        logger.info(f"Connected to MySQL database '{config.MYSQL_DB}' at {config.MYSQL_HOST}:{config.MYSQL_PORT}")

        async with _db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Create user_states table for FSM persistence
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_states (
                        user_id VARCHAR(64) PRIMARY KEY,
                        state VARCHAR(128) NULL,
                        data JSON NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
                # Create user_activity_log table
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_activity_log (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        user_id VARCHAR(64) NOT NULL,
                        action VARCHAR(128) NOT NULL,
                        payload TEXT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
        logger.info("MySQL tables initialized successfully.")
    except Exception as exc:
        logger.warning(f"Could not connect to MySQL: {exc}")
        _db_pool = None


async def get_db_pool() -> Optional[aiomysql.Pool]:
    """Returns the active MySQL connection pool."""
    return _db_pool
