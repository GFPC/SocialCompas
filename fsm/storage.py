import json
import logging
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger("fsm.storage")


class BaseFSMStorage(ABC):
    @abstractmethod
    async def set_state(self, user_id: str, state: Optional[str]) -> None:
        pass

    @abstractmethod
    async def get_state(self, user_id: str) -> Optional[str]:
        pass

    @abstractmethod
    async def set_data(self, user_id: str, data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def get_data(self, user_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def clear(self, user_id: str) -> None:
        pass


class MemoryStorage(BaseFSMStorage):
    """In-memory FSM Storage implementation."""

    def __init__(self):
        self._states: Dict[str, Optional[str]] = {}
        self._data: Dict[str, Dict[str, Any]] = {}

    async def set_state(self, user_id: str, state: Optional[str]) -> None:
        self._states[user_id] = state

    async def get_state(self, user_id: str) -> Optional[str]:
        return self._states.get(user_id)

    async def set_data(self, user_id: str, data: Dict[str, Any]) -> None:
        self._data[user_id] = data

    async def get_data(self, user_id: str) -> Dict[str, Any]:
        return self._data.get(user_id, {})

    async def clear(self, user_id: str) -> None:
        self._states.pop(user_id, None)
        self._data.pop(user_id, None)


class RedisFSMStorage(BaseFSMStorage):
    """Redis-backed FSM Storage implementation."""

    def __init__(self, redis_client):
        self.redis = redis_client

    def _state_key(self, user_id: str) -> str:
        return f"fsm:state:{user_id}"

    def _data_key(self, user_id: str) -> str:
        return f"fsm:data:{user_id}"

    async def set_state(self, user_id: str, state: Optional[str]) -> None:
        if state is None:
            await self.redis.delete(self._state_key(user_id))
        else:
            await self.redis.set(self._state_key(user_id), str(state))

    async def get_state(self, user_id: str) -> Optional[str]:
        return await self.redis.get(self._state_key(user_id))

    async def set_data(self, user_id: str, data: Dict[str, Any]) -> None:
        await self.redis.set(self._data_key(user_id), json.dumps(data, ensure_ascii=False))

    async def get_data(self, user_id: str) -> Dict[str, Any]:
        raw = await self.redis.get(self._data_key(user_id))
        if raw:
            return json.loads(raw)
        return {}

    async def clear(self, user_id: str) -> None:
        await self.redis.delete(self._state_key(user_id), self._data_key(user_id))


class MySQLFSMStorage(BaseFSMStorage):
    """MySQL-backed FSM Storage implementation."""

    def __init__(self, pool):
        self.pool = pool

    async def set_state(self, user_id: str, state: Optional[str]) -> None:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO user_states (user_id, state) VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE state = %s;
                    """,
                    (user_id, str(state) if state else None, str(state) if state else None),
                )

    async def get_state(self, user_id: str) -> Optional[str]:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT state FROM user_states WHERE user_id = %s;", (user_id,))
                row = await cur.fetchone()
                return row[0] if row else None

    async def set_data(self, user_id: str, data: Dict[str, Any]) -> None:
        json_data = json.dumps(data, ensure_ascii=False)
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO user_states (user_id, data) VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE data = %s;
                    """,
                    (user_id, json_data, json_data),
                )

    async def get_data(self, user_id: str) -> Dict[str, Any]:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT data FROM user_states WHERE user_id = %s;", (user_id,))
                row = await cur.fetchone()
                if row and row[0]:
                    return json.loads(row[0]) if isinstance(row[0], str) else row[0]
                return {}

    async def clear(self, user_id: str) -> None:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM user_states WHERE user_id = %s;", (user_id,))
