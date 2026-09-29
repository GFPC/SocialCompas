"""Reloads the places catalog from data/*.xlsx (DELETES all places and, via FK cascade, users' favorites).

    docker exec socialcompas_app python scripts/import_excel.py

The catalog is also imported automatically on the first start with an empty database.
After a re-import place ids change and map points must be recomputed (this script does it).
"""
import asyncio
import os
import sys

import aiomysql

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))
import config
from storage.catalog import parse_excel_rows, import_catalog, geocode_missing_places


async def main():
    rows = parse_excel_rows()
    if not rows:
        sys.exit("Не найдены файлы data/*.xlsx")
    pool = await aiomysql.create_pool(
        host=config.MYSQL_HOST, port=config.MYSQL_PORT, user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD, db=config.MYSQL_DB, autocommit=True,
    )
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            n = await import_catalog(cur, rows, replace=True)
    print(f"Импортировано записей: {n}")
    stats = await geocode_missing_places(pool)
    print(f"Метки на карте: {stats}")
    pool.close()
    await pool.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
