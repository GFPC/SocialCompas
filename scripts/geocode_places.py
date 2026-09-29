"""Computes map points (places.points) from addresses via OpenStreetMap Nominatim (~1 request/s).

    docker exec socialcompas_app python scripts/geocode_places.py [--force] [--retry-empty]

Runs automatically in the background at application start for places that were never geocoded.
--retry-empty  also retry places where nothing was found before; --force  recompute everything.
"""
import asyncio
import os
import sys

import aiomysql

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))
import config
from storage.catalog import geocode_missing_places


async def main():
    pool = await aiomysql.create_pool(
        host=config.MYSQL_HOST, port=config.MYSQL_PORT, user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD, db=config.MYSQL_DB, autocommit=True,
    )
    stats = await geocode_missing_places(pool, force="--force" in sys.argv, retry_empty="--retry-empty" in sys.argv)
    print(f"Готово: {stats}")
    pool.close()
    await pool.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
