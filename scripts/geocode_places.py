"""One-off / re-runnable geocoding: fills places.points (JSON list of {lat, lng, address}).

Uses OpenStreetMap Nominatim (1 request/sec policy). Already geocoded places are skipped
unless --force is passed. Run inside the app container:
    docker exec socialcompas_app python scripts/geocode_places.py
"""
import asyncio
import json
import os
import re
import sys

import aiomysql
import httpx

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))
import config

CITY_BOX = {  # lon_min, lat_max, lon_max, lat_min
    "Москва": (36.8, 56.1, 38.3, 55.1),
    "Санкт-Петербург": (29.4, 60.3, 31.1, 59.6),
    "Новосибирск": (82.5, 55.3, 83.4, 54.7),
}
NOMINATIM = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "SocialCompass-hackathon/1.0 (geocode script)"}


def split_addresses(address: str):
    return [a.strip() for a in re.split(r"[;\n]+", address or "") if a.strip()]


def variants(city: str, address: str):
    """Progressively simpler queries: full, normalized, street + house number, street only."""
    a = re.sub(r"\(.*?\)", "", address)                      # (цокольный этаж), (ТРК ...)
    a = a.split(" - ")[-1]                                     # "Большой зал - Невский пр., 30"
    a = re.sub(r"\b(оф|пом|кв|эт|ком)\.?\s*[\w\-/]+", "", a, flags=re.I)
    a = re.sub(r"\b(ТРК|ТРЦ|ТЦ)\b.*?,", "", a, flags=re.I)
    a = re.sub(r"\bд(ом)?\.?\s*(?=\d)", "", a, flags=re.I)     # д.5 -> 5
    a = re.sub(r"(\d+)\s*[кc]\.?\s*\d+.*$", r"\1", a, flags=re.I)  # 2к1 / 1с99 -> 2 / 1
    a = re.sub(r",\s*(стр|с|к|корп)\.?\s*\d+.*$", "", a, flags=re.I)  # ", с.7" / ", стр. 5"
    a = re.sub(r"\s+", " ", a).strip(" ,")
    street_num = re.match(r"^(.*?\d+[а-яa-z]?)(?![\d/])", a, flags=re.I)
    street_only = re.sub(r"[,\s]*\d.*$", "", a).strip(" ,")
    cands = [f"{address}, {city}", f"{a}, {city}"]
    if street_num:
        cands.append(f"{street_num.group(1)}, {city}")
    if street_only and re.search(r"(ул|пр|наб|пер|ш|бул|пл|аллея|линия)\b", street_only, flags=re.I):
        cands.append(f"{street_only}, {city}")
    seen, res = set(), []
    for q in cands:
        if q not in seen:
            seen.add(q)
            res.append(q)
    return res


async def geocode(client: httpx.AsyncClient, city: str, address: str):
    box = CITY_BOX.get(city)
    for q in variants(city, address):
        params = {"q": q, "format": "json", "limit": 1, "countrycodes": "ru"}
        if box:
            params.update(viewbox=",".join(map(str, box)), bounded=1)
        try:
            r = await client.get(NOMINATIM, params=params, headers=HEADERS)
            data = r.json() if r.status_code == 200 else []
        except Exception as exc:
            print(f"   ! {exc}")
            data = []
        await asyncio.sleep(1.1)
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    return None


async def main(force: bool):
    conn = await aiomysql.connect(
        host=config.MYSQL_HOST, port=config.MYSQL_PORT, user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD, db=config.MYSQL_DB, autocommit=True,
    )
    async with conn.cursor(aiomysql.DictCursor) as cur:
        try:
            await cur.execute("ALTER TABLE places ADD COLUMN points TEXT NULL;")
        except Exception:
            pass
        await cur.execute("SELECT id, city, title, address, points FROM places;")
        rows = await cur.fetchall()

    ok = fail = 0
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        for row in rows:
            if row["points"] not in (None, "", "[]") and not force:
                continue
            addrs = split_addresses(row["address"])
            points = []
            for a in addrs:
                res = await geocode(client, row["city"], a)
                if res:
                    points.append({"lat": res[0], "lng": res[1], "address": a})
                    ok += 1
                else:
                    fail += 1
                    print(f"   ✗ не найден: [{row['city']}] {row['title']} — {a}")
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE places SET points = %s WHERE id = %s;",
                    (json.dumps(points, ensure_ascii=False), row["id"]),
                )
            print(f"#{row['id']} {row['title']}: {len(points)}/{len(addrs)}")
    conn.close()
    print(f"\nГотово: найдено {ok}, не найдено {fail}")


if __name__ == "__main__":
    asyncio.run(main("--force" in sys.argv))
