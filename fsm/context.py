from typing import Any, Dict, Optional
from fsm.storage import BaseFSMStorage
from fsm.state import State


class FSMContext:
    """
    Context interface for getting and setting user state and state data.
    """

    def __init__(self, storage: BaseFSMStorage, user_id: str):
        self.storage = storage
        self.user_id = user_id

    async def set_state(self, state: Optional[State | str]) -> None:
        state_name = state.name if isinstance(state, State) else state
        await self.storage.set_state(self.user_id, state_name)

    async def get_state(self) -> Optional[str]:
        return await self.storage.get_state(self.user_id)

    async def set_data(self, data: Dict[str, Any]) -> None:
        await self.storage.set_data(self.user_id, data)

    async def get_data(self) -> Dict[str, Any]:
        return await self.storage.get_data(self.user_id)

    async def update_data(self, **kwargs) -> Dict[str, Any]:
        data = await self.get_data()
        data.update(kwargs)
        await self.set_data(data)
        return data

    async def clear(self) -> None:
        await self.storage.clear(self.user_id)
