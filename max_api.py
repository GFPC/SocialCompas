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
        async with httpx.AsyncClient(timeout=35.0, verify=False) as client:
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
    ) -> Dict[str, Any]:
        """
        Send message to a chat or user in MAX Messenger.
        Endpoint: POST /messages?chat_id={chat_id}
        """
        payload: Dict[str, Any] = {"text": text}
        if reply_markup:
            # Check if reply_markup is already a MAX attachment or raw keyboard
            if "attachments" in reply_markup:
                payload["attachments"] = reply_markup["attachments"]
            elif "type" in reply_markup:
                payload["attachments"] = [reply_markup]
            elif "inline_keyboard" in reply_markup:
                # Convert legacy telegram format to MAX attachment
                max_buttons = []
                for row in reply_markup["inline_keyboard"]:
                    max_row = []
                    for btn in row:
                        max_row.append({
                            "type": "callback",
                            "text": btn.get("text", ""),
                            "payload": btn.get("callback_data", btn.get("text", ""))
                        })
                    max_buttons.append(max_row)
                payload["attachments"] = [{
                    "type": "inline_keyboard",
                    "payload": {"buttons": max_buttons}
                }]

        params = {"chat_id": chat_id}
        return await self._request("POST", "/messages", payload=payload, params=params)

    async def answer_callback_query(self, callback_id: str, text: Optional[str] = None) -> Dict[str, Any]:
        """
        Respond to an inline button click (callback query).
        """
        params = {"callback_id": callback_id}
        payload = {}
        if text:
            payload["message"] = {"text": text}
        return await self._request("POST", "/answers", payload=payload, params=params)

    async def get_updates(self, marker: Optional[int] = None, limit: int = 100, timeout: int = 30) -> Dict[str, Any]:
        """
        Long-polling updates retrieval.
        Endpoint: GET /updates?marker={marker}&limit={limit}&timeout={timeout}
        """
        params = {"limit": limit, "timeout": timeout}
        if marker is not None:
            params["marker"] = marker
        return await self._request("GET", "/updates", params=params)

    async def get_subscriptions(self) -> Dict[str, Any]:
        """Get active webhook subscriptions."""
        return await self._request("GET", "/subscriptions")

    async def delete_subscriptions(self, url: Optional[str] = None) -> Dict[str, Any]:
        """Delete webhook subscriptions to enable long-polling."""
        subs = await self.get_subscriptions()
        for sub in subs.get("subscriptions", []):
            sub_url = sub.get("url")
            if not url or sub_url == url:
                await self._request("DELETE", "/subscriptions", params={"url": sub_url})
        return {"ok": True}

    async def set_webhook(self, url: str) -> Dict[str, Any]:
        """Register webhook subscription."""
        # Delete old subscriptions first
        await self.delete_subscriptions()
        payload = {
            "url": url,
            "update_types": ["message_created", "message_callback", "bot_started"]
        }
        return await self._request("POST", "/subscriptions", payload=payload)


def build_keyboard(buttons: List[List[Dict[str, str]]]) -> Dict[str, Any]:
    """
    Helper utility to construct inline keyboard markups for MAX Messenger.
    Each button is a dict: {"text": "Label", "callback_data": "action_id"}
    Returns MAX attachments format for inline_keyboard.
    """
    max_buttons = []
    for row in buttons:
        row_buttons = []
        for btn in row:
            row_buttons.append({
                "type": "callback" if "url" not in btn else "link",
                "text": btn.get("text", ""),
                "payload" if "url" not in btn else "url": btn.get("callback_data", btn.get("url", btn.get("text", "")))
            })
        max_buttons.append(row_buttons)

    return {
        "attachments": [
            {
                "type": "inline_keyboard",
                "payload": {
                    "buttons": max_buttons
                }
            }
        ]
    }
