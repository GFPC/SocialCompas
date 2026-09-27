import logging
import time
from typing import List, Optional, Dict
import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

import config
from storage.db import get_places_by_filter

logger = logging.getLogger("api.v1.chat")
router = APIRouter(prefix="/chat", tags=["AI Chat Assistant"])

# In-memory rate limiter per IP/client: client_ip -> list of timestamps
_rate_limit_records: Dict[str, List[float]] = {}


class ChatMessage(BaseModel):
    role: str = Field(..., description="Роль: 'user' или 'assistant'")
    content: str = Field(..., description="Текст сообщения")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="История сообщений диалога")
    city: Optional[str] = Field("Москва", description="Текущий выбранный город")
    category: Optional[str] = Field("Студенты", description="Текущая льготная категория")


def check_rate_limit(client_id: str):
    """
    Enforces rate limit of N requests per minute per IP address.
    """
    now = time.time()
    window_start = now - 60.0

    # Clean old timestamps
    if client_id in _rate_limit_records:
        _rate_limit_records[client_id] = [t for t in _rate_limit_records[client_id] if t > window_start]
    else:
        _rate_limit_records[client_id] = []

    if len(_rate_limit_records[client_id]) >= config.CHAT_RATE_LIMIT_PER_MINUTE:
        logger.warning(f"Rate limit exceeded for client {client_id}")
        raise HTTPException(
            status_code=429,
            detail=f"Превышен лимит запросов к ИИ (максимум {config.CHAT_RATE_LIMIT_PER_MINUTE} в минуту). Пожалуйста, подождите немного."
        )

    _rate_limit_records[client_id].append(now)


@router.post("")
async def generate_ai_response(req_data: ChatRequest, request: Request):
    """
    Генерирует ответ ИИ-ассистента SocialCompass через AI Tunnel API с обогащением данными из базы и лимитом запросов.
    """
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)

    if not req_data.messages:
        raise HTTPException(status_code=400, detail="Список сообщений не может быть пустым")

    # Fetch context places from DB
    places_context = ""
    try:
        places = await get_places_by_filter(req_data.city, req_data.category)
        if places:
            places_summary = []
            for p in places[:8]:
                places_summary.append(
                    f"• {p.get('title')} ({p.get('place_type', 'Место')}) — {p.get('promo_text', 'Скидки по удостоверению')}. Адрес: {p.get('address', 'в городе')}"
                )
            places_context = "\n".join(places_summary)
    except Exception as exc:
        logger.warning(f"Could not load places context for AI: {exc}")

    system_prompt = (
        "Ты — гид-ассистент сервиса SocialCompass (Социальный Компас). "
        "Твоя задача — помогать пользователям находить акции, скидки, льготы и интересные места досуга для категорий: "
        "Студенты, Пенсионеры и Участники СВО в городах Москва, Санкт-Петербург и Новосибирск.\n\n"
        f"Пользователь находится в городе: '{req_data.city}', Категория: '{req_data.category}'.\n"
    )

    if places_context:
        system_prompt += f"\nАктуальные места из нашей базы данных в городе {req_data.city} для категории {req_data.category}:\n{places_context}\n\n"

    system_prompt += (
        "Инструкции по ответу:\n"
        "1. Отвечай кратко, вежливо и дружелюбно на русском языке.\n"
        "2. Используй информацию из приведенной базы данных, когда пользователь спрашивает про конкретные места или скидки.\n"
        "3. Если пользователь спрашивает о чем-то другом, дай полезный совет и напомни про возможности сервиса SocialCompass.\n"
        "4. Форматируй текст аккуратно с помощью эмодзи и абзацев."
    )

    formatted_messages = [{"role": "system", "content": system_prompt}]
    for m in req_data.messages[-6:]: # Keep last 6 context messages
        role = "assistant" if m.role in ("assistant", "ai") else "user"
        formatted_messages.append({"role": role, "content": m.content})

    headers = {
        "Authorization": f"Bearer {config.AITUNNEL_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": config.AI_MODEL,
        "messages": formatted_messages,
        "max_tokens": 500,
        "temperature": 0.7
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{config.AITUNNEL_BASE_URL}/chat/completions",
                json=payload,
                headers=headers
            )
            if resp.status_code != 200:
                logger.error(f"AI Tunnel API error status {resp.status_code}: {resp.text}")
                raise HTTPException(status_code=502, detail="Сервис ИИ временно недоступен. Попробуйте позже.")

            data = resp.json()
            answer = data["choices"][0]["message"]["content"]
            return {"ok": True, "message": answer}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error communicating with AI Tunnel: {exc}")
        raise HTTPException(status_code=500, detail="Ошибка обработки запроса к ИИ")
