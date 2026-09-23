from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from storage.db import get_user_profile, save_user_profile
from core.auth import get_current_user

router = APIRouter(prefix="/profile", tags=["Profile"])


class ProfileUpdateMeRequest(BaseModel):
    city: str
    category: str


class ProfileUpdateRequest(BaseModel):
    user_id: str
    city: str
    category: str


@router.get("/me")
async def get_my_profile(current_user: str = Depends(get_current_user)):
    """
    Возвращает профиль (город и категорию) текущего авторизованного пользователя.
    """
    profile = await get_user_profile(current_user)
    if not profile:
        # Return default if not set
        return {"ok": True, "profile": {"city": "Москва", "category": "Студенты"}}
    return {"ok": True, "profile": profile}


@router.post("/me")
async def update_my_profile(req: ProfileUpdateMeRequest, current_user: str = Depends(get_current_user)):
    """
    Обновляет профиль (город и категорию) текущего авторизованного пользователя.
    """
    await save_user_profile(current_user, req.city, req.category)
    return {"ok": True, "message": "Профиль успешно обновлен"}


# Legacy compatibility routes
@router.get("/{user_id}")
async def get_profile_legacy(user_id: str):
    """
    Совместимый эндпоинт получения профиля пользователя по user_id.
    """
    profile = await get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Профиль пользователя не найден")
    return {"ok": True, "profile": profile}


@router.post("")
async def update_profile_legacy(req: ProfileUpdateRequest):
    """
    Совместимый эндпоинт обновления профиля пользователя.
    """
    await save_user_profile(req.user_id, req.city, req.category)
    return {"ok": True, "message": "Профиль успешно обновлен"}
