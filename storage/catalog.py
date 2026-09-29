"""Catalog of places: import from the Excel files in data/ and geocoding of addresses into map points.

Used both at application start-up (first run: empty DB → real catalog + map markers, no manual steps)
and by the CLI scripts scripts/import_excel.py and scripts/geocode_places.py.
"""
import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiomysql
import httpx

logger = logging.getLogger("storage.catalog")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EXCEL_FILES = [DATA_DIR / "БД акции по городам.xlsx", DATA_DIR / "Санкт-Петербург.xlsx"]

INSERT_SQL = """
    INSERT INTO places (city, category, title, description, place_type, promo_text, schedule, address, map_url)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
"""


# ── Excel import ─────────────────────────────────────────────────────────────

def _normalize_city(raw: str) -> str:
    low = raw.lower()
    if "петербург" in low or "спб" in low:
        return "Санкт-Петербург"
    if "новосибирск" in low:
        return "Новосибирск"
    if "москва" in low:
        return "Москва"
    return raw


def _normalize_category(raw: str) -> str:
    low = raw.lower()
    if "студент" in low:
        return "Студенты"
    if "пенсион" in low:
        return "Пенсионеры"
    if "сво" in low or "участник" in low:
        return "Участники СВО"
    return raw


def parse_excel_rows(paths: Optional[List[Path]] = None) -> List[Tuple[Any, ...]]:
    """Reads the catalog Excel files → rows ready for INSERT_SQL. Missing files are skipped."""
    import openpyxl

    rows_out: List[Tuple[Any, ...]] = []
    for path in paths or EXCEL_FILES:
        path = Path(path)
        if not path.exists():
            continue
        sheet = openpyxl.load_workbook(path, read_only=True).active
        count = 0
        for row in list(sheet.iter_rows(values_only=True))[1:]:
            if not row or not row[0] or len(row) < 3 or not row[2]:
                continue

            def cell(i: int, default: str = "") -> str:
                return str(row[i]).strip() if len(row) > i and row[i] else default

            promo = cell(4)
            rows_out.append((
                _normalize_city(str(row[0]).strip()),
                _normalize_category(cell(1, "Все")),
                str(row[2]).strip(),
                promo,                       # description (NOT NULL in older schemas)
                cell(3, "Место"),
                promo,
                cell(5),
                cell(6),
                cell(7, "https://max.ru"),
            ))
            count += 1
        logger.info(f"Parsed {count} places from {path.name}")
    return rows_out


async def import_catalog(cur, rows: List[Tuple[Any, ...]], replace: bool = False) -> int:
    if replace:
        await cur.execute("DELETE FROM places;")
    await cur.executemany(INSERT_SQL, rows)
    return len(rows)


# ── Geocoding (OpenStreetMap Nominatim, ≤ 1 request/second) ─────────────────

CITY_BOX = {  # lon_min, lat_max, lon_max, lat_min
    "Москва": (36.8, 56.1, 38.3, 55.1),
    "Санкт-Петербург": (29.4, 60.3, 31.1, 59.6),
    "Новосибирск": (82.5, 55.3, 83.4, 54.7),
}
NOMINATIM = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "SocialCompass-hackathon/1.0 (catalog geocoder)"}


def split_addresses(address: Optional[str]) -> List[str]:
    return [a.strip() for a in re.split(r"[;\n]+", address or "") if a.strip()]


def query_variants(city: str, address: str) -> List[str]:
    """Progressively simpler queries: full, normalized, street + house number, street only."""
    a = re.sub(r"\(.*?\)", "", address)                       # (цокольный этаж), (ТРК ...)
    a = a.split(" - ")[-1]                                    # "Большой зал - Невский пр., 30"
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


async def geocode_address(client: httpx.AsyncClient, city: str, address: str) -> Optional[Tuple[float, float]]:
    box = CITY_BOX.get(city)
    for q in query_variants(city, address):
        params: Dict[str, Any] = {"q": q, "format": "json", "limit": 1, "countrycodes": "ru"}
        if box:
            params.update(viewbox=",".join(map(str, box)), bounded=1)
        data: list = []
        try:
            r = await client.get(NOMINATIM, params=params, headers=HEADERS)
            data = r.json() if r.status_code == 200 else []
        except Exception as exc:
            logger.warning(f"Geocoder request failed: {exc}")
        await asyncio.sleep(1.1)  # Nominatim usage policy
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    return None


async def geocode_missing_places(pool: aiomysql.Pool, force: bool = False, retry_empty: bool = False) -> Dict[str, int]:
    """
    Fills places.points (JSON [{lat, lng, address}]) for places that have none yet.
    NULL = never geocoded; '[]' = tried, nothing found (skipped unless retry_empty/force).
    """
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT id, city, title, address, points FROM places;")
            rows = await cur.fetchall()

    todo = []
    for row in rows:
        p = row["points"]
        if force or p in (None, "") or (retry_empty and p == "[]"):
            todo.append(row)
    stats = {"places": len(todo), "found": 0, "missing": 0}
    if not todo:
        return stats

    logger.info(f"Geocoding {len(todo)} places (OpenStreetMap Nominatim, ~1 request/s)…")
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        for row in todo:
            points = []
            for addr in split_addresses(row["address"]):
                res = await geocode_address(client, row["city"], addr)
                if res:
                    points.append({"lat": res[0], "lng": res[1], "address": addr})
                    stats["found"] += 1
                else:
                    stats["missing"] += 1
                    logger.info(f"Geocoder: not found [{row['city']}] {row['title']} — {addr}")
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "UPDATE places SET points = %s WHERE id = %s;",
                        (json.dumps(points, ensure_ascii=False), row["id"]),
                    )
    logger.info(f"Geocoding finished: {stats}")
    return stats
