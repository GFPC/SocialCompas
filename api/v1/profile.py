from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from storage.db import get_user_profile, save_user_profile
from core.auth import get_current_user, get_path_user, authorize_user_access, security

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
async def get_profile_by_id(user_id: str = Depends(get_path_user)):
    """
    Возвращает профиль пользователя по user_id (требуется Bearer-токен этого пользователя).
    """
    profile = await get_user_profile(user_id)
    return {"ok": True, "profile": profile}


@router.post("")
@router.post("/")
async def update_profile_general(
    req: ProfileUpdateRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
):
    """
    Сохраняет профиль по переданному user_id (MAX user id из initData).
    """
    if not req.user_id:
        raise HTTPException(status_code=400, detail="user_id обязателен")
    authorize_user_access(req.user_id, credentials)
    await save_user_profile(req.user_id, req.city, req.category)
    return {"ok": True, "message": "Профиль успешно сохранен", "user_id": req.user_id}


@router.post("/{user_id}")
async def update_profile_by_id(req: ProfileUpdateRequest, user_id: str = Depends(get_path_user)):
    """
    Обновляет профиль для конкретного user_id.
    """
    await save_user_profile(user_id, req.city, req.category)
    return {"ok": True, "message": "Профиль успешно сохранен", "user_id": user_id}
