from fastapi import APIRouter, HTTPException
from storage.db import get_user_favorites, add_favorite, remove_favorite

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.get("/{user_id}")
async def list_favorites(user_id: str):
    """Возвращает избранные места пользователя."""
    favorites = await get_user_favorites(user_id)
    return {"ok": True, "count": len(favorites), "items": favorites}


@router.post("/{user_id}/{place_id}")
async def add_to_favorites(user_id: str, place_id: int):
    """Добавляет место в избранное."""
    await add_favorite(user_id, place_id)
    return {"ok": True, "message": "Место добавлено в избранное"}


@router.delete("/{user_id}/{place_id}")
async def remove_from_favorites(user_id: str, place_id: int):
    """Удаляет место из избранного."""
    await remove_favorite(user_id, place_id)
    return {"ok": True, "message": "Место удалено из избранного"}
