from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from storage.db import get_user_profile, save_user_profile

router = APIRouter(prefix="/profile", tags=["Profile"])


class ProfileUpdateRequest(BaseModel):
    user_id: str
    city: str
    category: str


@router.get("/{user_id}")
async def get_profile(user_id: str):
    """Возвращает профиль пользователя (город и категория)."""
    profile = await get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Профиль пользователя не найден")
    return {"ok": True, "profile": profile}


@router.post("")
async def update_profile(req: ProfileUpdateRequest):
    """Обновляет или создает профиль пользователя."""
    await save_user_profile(req.user_id, req.city, req.category)
    return {"ok": True, "message": "Профиль успешно обновлен"}
