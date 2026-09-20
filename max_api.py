import logging
from typing import Any, Dict, List, Optional
import httpx

import config

logger = logging.getLogger("max_api")
logging.basicConfig(level=logging.INFO)


class MaxBotAPI:
    """
    Client for interacting with MAX Messenger Bot API (v2 endpoint).
    Base URL: https://platform-api2.max.ru
    Authorization: <MAX_BOT_TOKEN>
    """

    def __init__(self, token: str = config.MAX_BOT_TOKEN, api_url: str = config.MAX_API_URL):
        self.token = token
        self.api_url = api_url.rstrip("/")
        self.headers = {
            "Authorization": self.token,
            "Content-Type": "application/json",
            "User-Agent": "SocialCompas-MaxBot/1.0",
        }

    async def _request(self, method: str, endpoint: str, payload: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.api_url}{endpoint}"
        async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=payload,
                    params=params,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                logger.error(f"HTTP Error {exc.response.status_code} calling {url}: {exc.response.text}")
                return {"ok": False, "error_code": exc.response.status_code, "description": exc.response.text}
            except Exception as exc:
                logger.error(f"Request exception calling {url}: {exc}")
                return {"ok": False, "description": str(exc)}

    async def get_me(self) -> Dict[str, Any]:
        """Fetch bot info."""
        return await self._request("GET", "/me")

    async def send_message(
        self,
        chat_id: str | int,
        text: str,
        reply_markup: Optional[Dict[str, Any]] = None,
        parse_mode: str = "Markdown",
    ) -> Dict[str, Any]:
        """
        Send message to a user or chat.
        """
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        return await self._request("POST", "/sendMessage", payload=payload)

    async def answer_callback_query(self, callback_query_id: str, text: Optional[str] = None, show_alert: bool = False) -> Dict[str, Any]:
        """
        Respond to an inline button click (callback query).
        """
        payload = {
            "callback_query_id": callback_query_id,
            "text": text,
            "show_alert": show_alert,
        }
        return await self._request("POST", "/answerCallbackQuery", payload=payload)

    async def set_webhook(self, url: str) -> Dict[str, Any]:
        """
        Register a webhook URL.
        """
        return await self._request("POST", "/setWebhook", payload={"url": url})

    async def get_updates(self, offset: int = 0, limit: int = 100, timeout: int = 30) -> Dict[str, Any]:
        """
        Long-polling updates retrieval.
        """
        params = {"offset": offset, "limit": limit, "timeout": timeout}
        return await self._request("GET", "/getUpdates", params=params)


def build_keyboard(buttons: List[List[Dict[str, str]]]) -> Dict[str, Any]:
    """
    Helper utility to construct inline keyboard markups for MAX Messenger.
    Each button is a dict: {"text": "Label", "callback_data": "action_id"}
    """
    inline_keyboard = []
    for row in buttons:
        row_buttons = []
        for btn in row:
            row_buttons.append({
                "text": btn.get("text", ""),
                "callback_data": btn.get("callback_data", btn.get("text", ""))
            })
        inline_keyboard.append(row_buttons)
    return {"inline_keyboard": inline_keyboard}
