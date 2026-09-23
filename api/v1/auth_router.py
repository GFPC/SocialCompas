from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.auth import create_user_token, verify_webapp_init_data

router = APIRouter(prefix="/auth", tags=["Auth"])


class WebAppAuthRequest(BaseModel):
    init_data: str


class TokenRequest(BaseModel):
    user_id: str


@router.post("/webapp")
async def webapp_auth(req: WebAppAuthRequest):
    """
    Проверяет криптографическую подпись (HMAC-SHA256) строки WebApp initData от MAX Messenger / Telegram.
    При успешной проверке подписи генерирует подлинный токен авторизации для пользователя.
    """
    verified_data = verify_webapp_init_data(req.init_data)
    if not verified_data:
        raise HTTPException(
            status_code=401,
            detail="Недействительная или поддельная криптографическая подпись WebApp initData"
        )

    # Extract user_id from verified initData
    user_data = verified_data.get("user_data", {})
    user_id = str(user_data.get("id") or verified_data.get("user_id") or verified_data.get("query_id", "guest"))

    token = create_user_token(user_id)
    return {
        "ok": True,
        "user_id": user_id,
        "token": token,
        "expires_in": 2592000,
        "user": user_data
    }


@router.post("/token")
async def issue_token(req: TokenRequest):
    """
    Генерирует токен авторизации по user_id (для серверных тестов).
    """
    if not req.user_id or len(req.user_id.strip()) == 0:
        raise HTTPException(status_code=400, detail="Неверный user_id")

    token = create_user_token(req.user_id)
    return {"ok": True, "token": token, "expires_in": 2592000}
