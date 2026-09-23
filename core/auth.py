import hmac
import hashlib
import time
import base64
import json
import logging
from typing import Optional
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import config

logger = logging.getLogger("core.auth")
security = HTTPBearer(auto_error=False)

SECRET_KEY = getattr(config, "SECRET_KEY", config.MAX_BOT_TOKEN)


def create_user_token(user_id: str, expires_in: int = 86400 * 30) -> str:
    """
    Generates a secure, signed JWT-like token for a user.
    """
    payload = {
        "uid": str(user_id),
        "exp": int(time.time()) + expires_in
    }
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode('utf-8').rstrip('=')
    
    signature = hmac.new(SECRET_KEY.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"


def verify_user_token(token: str) -> Optional[str]:
    """
    Verifies a user token and returns the authenticated user_id if valid.
    """
    if not token or "." not in token:
        return None

    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None

        payload_b64, signature = parts[0], parts[1]

        # Verify HMAC signature
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            logger.warning("Invalid token signature detected!")
            return None

        # Decode payload
        padded_b64 = payload_b64 + '=' * (-len(payload_b64) % 4)
        payload_data = json.loads(base64.urlsafe_b64decode(padded_b64).decode('utf-8'))

        # Check expiration
        if payload_data.get("exp", 0) < time.time():
            logger.warning("Expired token used!")
            return None

        return str(payload_data.get("uid"))
    except Exception as exc:
        logger.error(f"Error verifying token: {exc}")
        return None


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> str:
    """
    FastAPI dependency to extract and authenticate the current user from Bearer Token.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Отсутствует заголовок авторизации (Authorization: Bearer <token>)")

    token = credentials.credentials
    user_id = verify_user_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Недействительный или просроченный токен авторизации")

    return user_id
