from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.auth import create_user_token

router = APIRouter(prefix="/auth", tags=["Auth"])


class TokenRequest(BaseModel):
    user_id: str


@router.post("/token")
async def issue_token(req: TokenRequest):
    """
    Генерирует защищенный токен авторизации (Bearer token) по user_id.
    Токен используется MiniApp для выполнения защищенных запросов (профиль, избранное).
    """
    if not req.user_id or len(req.user_id.strip()) == 0:
        raise HTTPException(status_code=400, detail="Неверный user_id")

    token = create_user_token(req.user_id)
    return {"ok": True, "token": token, "expires_in": 2592000}
