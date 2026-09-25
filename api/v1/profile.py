from fastapi import APIRouter, Depends
from pydantic import BaseModel
from storage.db import get_user_profile, save_user_profile
from core.auth import get_current_user

router = APIRouter(prefix="/profile", tags=["Profile"])


class ProfileUpdateMeRequest(BaseModel):
    city: str
    category: str


@router.get("/me")
async def get_my_profile(current_user: str = Depends(get_current_user)):
    """
    Возвращает профиль (город и категорию) авторизованного пользователя по JWT-току.
    """
    profile = await get_user_profile(current_user)
    if not profile:
        return {"ok": True, "profile": {"city": "Москва", "category": "Студенты"}}
    return {"ok": True, "profile": profile}


@router.post("/me")
async def update_my_profile(req: ProfileUpdateMeRequest, current_user: str = Depends(get_current_user)):
    """
    Обновляет профиль (город и категорию) авторизованного пользователя по JWT-току.
    """
    await save_user_profile(current_user, req.city, req.category)
    return {"ok": True, "message": "Профиль успешно обновлен"}
