import json
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from storage.db import get_places_by_filter, get_place_by_id

router = APIRouter(prefix="/places", tags=["Places"])


def _with_points(place: dict) -> dict:
    raw = place.get("points")
    try:
        place["points"] = json.loads(raw) if isinstance(raw, str) and raw else []
    except ValueError:
        place["points"] = []
    return place


@router.get("")
async def list_places(
    city: str = Query(..., description="Город (например, Москва, Новосибирск)"),
    category: str = Query(..., description="Категория (например, Участники СВО, Студенты, Пенсионеры)")
):
    """Возвращает список акций и мест по фильтрам города и категории."""
    places = await get_places_by_filter(city, category)
    places = [_with_points(p) for p in places]
    return {"ok": True, "count": len(places), "items": places}


@router.get("/{place_id}")
async def get_place_detail(place_id: int):
    """Возвращает подробную информацию о конкретном месте."""
    place = await get_place_by_id(place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Место не найдено")
    return {"ok": True, "place": _with_points(place)}
