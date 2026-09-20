import logging
from typing import Any, Dict, List, Optional
import httpx

import config

logger = logging.getLogger("transport")


class MaxBotTransport:
    """
    Dedicated Transport Layer client for MAX Messenger Bot API v2.
    Handles low-level HTTP requests, payload encoding, error retries, and callback answers.
    """

    def __init__(self, token: str = config.MAX_BOT_TOKEN, api_url: str = config.MAX_API_URL):
        self.token = token
        self.api_url = api_url.rstrip("/")
        self.headers = {
            "Authorization": self.token,
            "Content-Type": "application/json",
            "User-Agent": "SocialCompas-MaxTransport/2.0",
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
                logger.error(f"Transport HTTP Error {exc.response.status_code} on {url}: {exc.response.text}")
                return {"ok": False, "error_code": exc.response.status_code, "description": exc.response.text}
            except Exception as exc:
                logger.error(f"Transport exception on {url}: {exc}")
                return {"ok": False, "description": str(exc)}

    async def get_me(self) -> Dict[str, Any]:
        """Fetch bot info."""
        return await self._request("GET", "/me")

    async def send_message(
        self,
        chat_id: str | int,
        text: str,
        keyboard: Optional[List[List[Dict[str, str]]]] = None,
    ) -> Dict[str, Any]:
        """
        Send a text message with optional inline keyboard and Markdown formatting.
        """
        payload: Dict[str, Any] = {
            "text": text,
            "format": "markdown"
        }

        if keyboard:
            max_buttons = []
            for row in keyboard:
                max_row = []
                for btn in row:
                    btn_type = "link" if "url" in btn else "callback"
                    item = {
                        "type": btn_type,
                        "text": btn.get("text", ""),
                    }
                    if btn_type == "link":
                        item["url"] = btn.get("url", "")
                    else:
                        item["payload"] = btn.get("callback_data", btn.get("text", ""))
                    max_row.append(item)
                max_buttons.append(max_row)

            payload["attachments"] = [
                {
                    "type": "inline_keyboard",
                    "payload": {
                        "buttons": max_buttons
                    }
                }
            ]

        params = {"chat_id": chat_id}
        return await self._request("POST", "/messages", payload=payload, params=params)

    async def answer_callback(self, callback_id: str, notification: str = "ОК") -> Dict[str, Any]:
        """
        Answers MAX callback query with notification string to prevent 400 Bad Request.
        """
        params = {"callback_id": callback_id}
        payload = {"notification": notification}
        return await self._request("POST", "/answers", payload=payload, params=params)

    async def get_updates(self, marker: Optional[int] = None, limit: int = 100, timeout: int = 25) -> Dict[str, Any]:
        """
        Fetches long-polling updates.
        """
        params = {"limit": limit, "timeout": timeout}
        if marker is not None:
            params["marker"] = marker
        return await self._request("GET", "/updates", params=params)

    async def delete_subscriptions(self) -> Dict[str, Any]:
        """Clears active webhook subscriptions for long polling mode."""
        subs = await self._request("GET", "/subscriptions")
        for sub in subs.get("subscriptions", []):
            if "url" in sub:
                await self._request("DELETE", "/subscriptions", params={"url": sub["url"]})
        return {"ok": True}
