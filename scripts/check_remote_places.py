import asyncio
import aiomysql
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
import config

async def run():
    pool = await aiomysql.create_pool(
        host=config.MYSQL_HOST,
        port=config.MYSQL_PORT,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        db=config.MYSQL_DB,
    )
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT DISTINCT city, category, COUNT(*) FROM places GROUP BY city, category;")
            rows = await cur.fetchall()
            print("=== DB Places breakdown ===")
            for r in rows:
                print(r)

    pool.close()
    await pool.wait_closed()

if __name__ == "__main__":
    asyncio.run(run())
