import hmac
import hashlib
import time
import base64
import json
import logging
from typing import Optional
from urllib.parse import parse_qsl
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


def verify_webapp_init_data(init_data: str, max_age: int = 86400) -> Optional[dict]:
    """
    Cryptographically verifies the HMAC signature of MAX/Telegram WebApp initData string.
    Returns parsed payload if signature is valid and not expired, else None.
    """
    if not init_data or "hash=" not in init_data:
        return None

    try:
        parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed_data.pop("hash", None)
        if not received_hash:
            return None

        # Sort key=value pairs alphabetically joined by \n
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))

        # Derive secret key using bot token
        bot_token = config.MAX_BOT_TOKEN
        secret_key = hmac.new(b"WebAppData", bot_token.encode('utf-8'), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode('utf-8'), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(received_hash, calculated_hash):
            logger.warning("Invalid WebApp initData HMAC signature!")
            return None

        # Check auth_date age (optional max_age check if auth_date present)
        auth_date = int(parsed_data.get("auth_date", 0))
        if auth_date > 0 and (time.time() - auth_date) > max_age:
            logger.warning("Expired WebApp initData auth_date!")
            return None

        # Parse user JSON field if available
        if "user" in parsed_data:
            try:
                parsed_data["user_data"] = json.loads(parsed_data["user"])
            except Exception:
                pass

        return parsed_data
    except Exception as exc:
        logger.error(f"Error validating WebApp initData: {exc}")
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
