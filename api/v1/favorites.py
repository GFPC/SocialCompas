from fastapi import APIRouter, Depends
from storage.db import get_user_favorites, add_favorite, remove_favorite
from core.auth import get_current_user

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.get("")
@router.get("/")
async def list_my_favorites(current_user: str = Depends(get_current_user)):
    """
    Возвращает избранные места авторизованного пользователя по JWT-токену.
    """
    favorites = await get_user_favorites(current_user)
    return {"ok": True, "count": len(favorites), "items": favorites}


@router.get("/{user_id}")
async def list_favorites_by_user(user_id: str):
    """
    Возвращает список избранного по user_id (для MiniApp / MAX Bot).
    """
    favorites = await get_user_favorites(user_id)
    return {"ok": True, "count": len(favorites), "items": favorites}


@router.post("/{place_id}")
async def add_my_favorite(place_id: int, current_user: str = Depends(get_current_user)):
    """
    Добавляет место в избранное авторизованного пользователя по JWT-токену.
    """
    await add_favorite(current_user, place_id)
    return {"ok": True, "message": "Место добавлено в избранное"}


@router.post("/{user_id}/{place_id}")
async def add_favorite_by_user(user_id: str, place_id: int):
    """
    Добавляет место в избранное конкретного user_id.
    """
    await add_favorite(user_id, place_id)
    return {"ok": True, "message": "Место добавлено в избранное"}


@router.delete("/{place_id}")
async def remove_my_favorite(place_id: int, current_user: str = Depends(get_current_user)):
    """
    Удаляет место из избранного авторизованного пользователя по JWT-токену.
    """
    await remove_favorite(current_user, place_id)
    return {"ok": True, "message": "Место удалено из избранного"}


@router.delete("/{user_id}/{place_id}")
async def remove_favorite_by_user(user_id: str, place_id: int):
    """
    Удаляет место из избранного конкретного user_id.
    """
    await remove_favorite(user_id, place_id)
    return {"ok": True, "message": "Место удалено из избранного"}
