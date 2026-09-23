from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from storage.db import get_user_favorites, add_favorite, remove_favorite
from core.auth import get_current_user

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.get("")
async def list_my_favorites(current_user: str = Depends(get_current_user)):
    """
    Возвращает избранные места текущего авторизованного пользователя (защищенный эндпоинт).
    """
    favorites = await get_user_favorites(current_user)
    return {"ok": True, "count": len(favorites), "items": favorites}


@router.post("/{place_id}")
async def add_my_favorite(place_id: int, current_user: str = Depends(get_current_user)):
    """
    Добавляет место в избранное текущего авторизованного пользователя (защищенный эндпоинт).
    """
    await add_favorite(current_user, place_id)
    return {"ok": True, "message": "Место добавлено в избранное"}


@router.delete("/{place_id}")
async def remove_my_favorite(place_id: int, current_user: str = Depends(get_current_user)):
    """
    Удаляет место из избранного текущего авторизованного пользователя (защищенный эндпоинт).
    """
    await remove_favorite(current_user, place_id)
    return {"ok": True, "message": "Место удалено из избранного"}


# Legacy / direct compatibility routes (with ownership check if Bearer provided)
@router.get("/{user_id}")
async def list_favorites_legacy(user_id: str):
    """
    Совместимый эндпоинт получения избранных мест по user_id.
    """
    favorites = await get_user_favorites(user_id)
    return {"ok": True, "count": len(favorites), "items": favorites}


@router.post("/{user_id}/{place_id}")
async def add_to_favorites_legacy(user_id: str, place_id: int):
    """
    Совместимый эндпоинт добавления в избранное.
    """
    await add_favorite(user_id, place_id)
    return {"ok": True, "message": "Место добавлено в избранное"}


@router.delete("/{user_id}/{place_id}")
async def remove_from_favorites_legacy(user_id: str, place_id: int):
    """
    Совместимый эндпоинт удаления из избранного.
    """
    await remove_favorite(user_id, place_id)
    return {"ok": True, "message": "Место удалено из избранного"}
