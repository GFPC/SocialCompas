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


async def get_ai_completion(messages: List[Dict[str, str]], city: str = "Москва", category: str = "Студенты") -> str:
    """
    Генерирует ответ ИИ через AI Tunnel API с ограничением по длине контекста и количеству токенов.
    """
    if not config.AITUNNEL_API_KEY or "YOUR_" in config.AITUNNEL_API_KEY:
        return "Я — ассистент сервиса SocialCompass 🧭. Чтобы включить онлайн-ИИ, укажите рабочий AITUNNEL_API_KEY в файле .env или переменных окружения."

    places_context = ""
    try:
        places = await get_places_by_filter(city, category)
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
        "Ты — дружелюбный и общительный ИИ-гид сервиса «Социальный Компас» (SocialCompass) 🧭.\n"
        "Твоя задача — открыто и вежливо помогать пользователям находить отличные места, интересные события, варианты досуга и отдыха, развлечения, а также рассказывать про скидки и льготы (для студентов, пенсионеров и участников СВО) в г. {city} (и других городах РФ).\n\n"
        "ПРИНЦИПЫ ОТВЕТА:\n"
        "1. Будь максимальной полезным и вежливым. Отвечай открыто на любые вопросы про досуг, отдых, места, куда сходить, что посмотреть, прогулки, культуру, скидки и события.\n"
        "2. Используй эмодзи, структурируй списки и предлагай конкретные идеи.\n"
        "3. Если пользователь задает вопрос, вообще не связанный с местами, досугом, путешествиями или скидками (например, просит написать код на Python или решить уравнение), в 1-2 предложении вежливо напомни, что ты ассистент SocialCompass 🧭 и специализируешься на поиске мест для отдыха и скидок.\n\n"
        f"КОНТЕКСТ ПОЛЬЗОВАТЕЛЯ:\n"
        f"• Город: '{city}'\n"
        f"• Категория: '{category}'\n"
    ).format(city=city, category=category)

    if places_context:
        system_prompt += f"\nМеста и акции из базы данных SocialCompass ({city}, {category}):\n{places_context}\n\n"

    formatted_messages = [{"role": "system", "content": system_prompt}]
    # Берем не более 6 последних сообщений диалога для экономии токенов
    for m in messages[-6:]:
        role = "assistant" if m.get("role") in ("assistant", "ai") else "user"
        raw_content = m.get("content") or m.get("text") or ""
        # Обрезаем каждое сообщение до 400 символов для предотвращения перерасхода токенов
        content = raw_content[:400] if len(raw_content) > 400 else raw_content
        formatted_messages.append({"role": role, "content": content})

    headers = {
        "Authorization": f"Bearer {config.AITUNNEL_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": config.AI_MODEL,
        "messages": formatted_messages,
        "max_tokens": 400,
        "temperature": 0.7
    }

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
        return data["choices"][0]["message"]["content"]


@router.post("")
async def generate_ai_response(req_data: ChatRequest, request: Request):
    """
    Генерирует ответ ИИ-ассистента SocialCompass через AI Tunnel API с обогащением данными из базы и лимитом запросов.
    """
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)

    if not req_data.messages:
        raise HTTPException(status_code=400, detail="Список сообщений не может быть пустым")

    raw_msgs = [{"role": m.role, "content": m.content} for m in req_data.messages]
    city = req_data.city or "Москва"
    category = req_data.category or "Студенты"

    try:
        answer = await get_ai_completion(raw_msgs, city=city, category=category)
        return {"ok": True, "message": answer}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error in generate_ai_response: {exc}")
        raise HTTPException(status_code=500, detail="Ошибка обработки запроса к ИИ")
