from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    update_type: str
    chat_id: str
    user_id: str
    raw_update: Dict[str, Any] = Field(default_factory=dict)


class MessageEvent(BaseEvent):
    update_type: str = "message_created"
    text: str = ""
    message_id: Optional[str] = None
    sender_name: Optional[str] = None


class CallbackEvent(BaseEvent):
    update_type: str = "message_callback"
    callback_id: str
    payload: str
    message_id: Optional[str] = None


class BotStartedEvent(BaseEvent):
    update_type: str = "bot_started"


def parse_update(update: Dict[str, Any]) -> Optional[BaseEvent]:
    """
    Parses a raw update dict into a strongly-typed event model.
    """
    update_type = update.get("update_type", "")

    if update_type == "bot_started":
        chat_id = str(update.get("chat_id") or update.get("user_id"))
        user_id = str(update.get("user_id") or chat_id)
        return BotStartedEvent(
            update_type=update_type,
            chat_id=chat_id,
            user_id=user_id,
            raw_update=update
        )

    if update_type == "message_callback" or "callback" in update:
        cb = update.get("callback", {})
        msg = update.get("message", {})
        recipient = msg.get("recipient", {})
        user = cb.get("user", {})
        chat_id = str(recipient.get("chat_id") or update.get("chat_id") or user.get("user_id", ""))
        user_id = str(user.get("user_id") or chat_id)
        callback_id = cb.get("callback_id", "")
        payload = cb.get("payload", cb.get("data", ""))

        return CallbackEvent(
            update_type="message_callback",
            chat_id=chat_id,
            user_id=user_id,
            callback_id=callback_id,
            payload=payload,
            message_id=msg.get("body", {}).get("mid"),
            raw_update=update
        )

    # Message event
    msg = update.get("message", update)
    recipient = msg.get("recipient", {})
    sender = msg.get("sender", {})
    chat_id = str(recipient.get("chat_id") or update.get("chat_id") or sender.get("user_id", ""))
    user_id = str(sender.get("user_id") or chat_id)

    body = msg.get("body", {})
    text = body.get("text") if isinstance(body, dict) else None
    if not text:
        text = msg.get("text", "").strip()

    return MessageEvent(
        update_type="message_created",
        chat_id=chat_id,
        user_id=user_id,
        text=text or "",
        message_id=body.get("mid") if isinstance(body, dict) else None,
        sender_name=sender.get("name") or sender.get("first_name"),
        raw_update=update
    )
