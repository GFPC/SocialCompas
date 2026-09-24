import asyncio
import aiomysql
import sys
import os

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))
import config

async def check():
    pool = await aiomysql.create_pool(
        host=config.MYSQL_HOST,
        port=config.MYSQL_PORT,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        db=config.MYSQL_DB,
        autocommit=True
    )
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT DISTINCT city, category FROM places;")
            rows = await cur.fetchall()
            print("DISTINCT COMBINATIONS IN PLACES:")
            for r in rows:
                print(r)
            
            await cur.execute("SELECT * FROM places LIMIT 1;")
            row = await cur.fetchone()
            print("\nSAMPLE PLACE ROW:")
            print(row)
            
    pool.close()
    await pool.wait_closed()

if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(check())
