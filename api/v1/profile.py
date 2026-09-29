from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from storage.db import get_user_profile, save_user_profile
from core.auth import get_current_user

router = APIRouter(prefix="/profile", tags=["Profile"])


class ProfileUpdateRequest(BaseModel):
    user_id: Optional[str] = None
    city: str
    category: str


@router.get("/me")
async def get_my_profile(current_user: str = Depends(get_current_user)):
    """
    Возвращает профиль (город и категорию) авторизованного пользователя по JWT-токену.
    """
    profile = await get_user_profile(current_user)
    if not profile:
        return {"ok": True, "profile": {"city": "Москва", "category": "Студенты"}}
    return {"ok": True, "profile": profile}


@router.post("/me")
async def update_my_profile(req: ProfileUpdateRequest, current_user: str = Depends(get_current_user)):
    """
    Обновляет профиль (город и категорию) авторизованного пользователя по JWT-токену.
    """
    await save_user_profile(current_user, req.city, req.category)
    return {"ok": True, "message": "Профиль успешно обновлен"}


@router.get("/{user_id}")
async def get_profile_by_id(user_id: str):
    """
    Возвращает профиль конкретного пользователя по user_id (для MiniApp/MAX Bot).
    """
    profile = await get_user_profile(user_id)
    return {"ok": True, "profile": profile}


@router.post("")
@router.post("/")
async def update_profile_general(req: ProfileUpdateRequest):
    """
    Сохраняет профиль по переданному user_id (MAX user id из initData).
    """
    if not req.user_id:
        raise HTTPException(status_code=400, detail="user_id обязателен")
    await save_user_profile(req.user_id, req.city, req.category)
    return {"ok": True, "message": "Профиль успешно сохранен", "user_id": req.user_id}


@router.post("/{user_id}")
async def update_profile_by_id(user_id: str, req: ProfileUpdateRequest):
    """
    Обновляет профиль для конкретного user_id.
    """
    await save_user_profile(user_id, req.city, req.category)
    return {"ok": True, "message": "Профиль успешно сохранен", "user_id": user_id}
