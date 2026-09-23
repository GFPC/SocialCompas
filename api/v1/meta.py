from fastapi import APIRouter
from storage.db import get_all_cities, get_all_categories

router = APIRouter(tags=["Metadata"])


@router.get("/cities")
async def list_cities():
    """
    Возвращает список всех доступных и активных городов в базе данных.
    Используется фронтендом MiniApp для динамического заполнения выбора города.
    """
    cities = await get_all_cities()
    return {"ok": True, "count": len(cities), "items": cities}


@router.get("/categories")
async def list_categories():
    """
    Возвращает список всех доступных категорий (льготников) в базе данных.
    Используется фронтендом MiniApp для динамического заполнения выбора категории.
    """
    categories = await get_all_categories()
    return {"ok": True, "count": len(categories), "items": categories}
