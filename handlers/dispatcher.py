import logging
from typing import Any, Callable, Dict, List, Optional, Tuple
from transport import MaxBotTransport, parse_update, BaseEvent, MessageEvent, CallbackEvent, BotStartedEvent
from fsm import BaseFSMStorage, FSMContext

logger = logging.getLogger("dispatcher")


class Dispatcher:
    """
    Central Event Dispatcher linking Transport, FSM, and Service logic.
    """

    def __init__(self, transport: MaxBotTransport, storage: BaseFSMStorage):
        self.transport = transport
        self.storage = storage
        self.message_handlers: List[Callable] = []
        self.callback_handlers: List[Callable] = []

    def get_fsm_context(self, user_id: str) -> FSMContext:
        return FSMContext(self.storage, user_id)

    async def feed_update(self, raw_update: Dict[str, Any]) -> None:
        """
        Parses raw update from transport and routes to appropriate handler.
        """
        event = parse_update(raw_update)
        if not event:
            logger.warning(f"Could not parse update: {raw_update}")
            return

        ctx = self.get_fsm_context(event.user_id)
        current_state = await ctx.get_state()

        if isinstance(event, CallbackEvent):
            # Acknowledge callback immediately in MAX API to clear loading indicator
            try:
                await self.transport.answer_callback(event.callback_id, notification="ОК")
            except Exception as e:
                logger.warning(f"Failed to acknowledge callback: {e}")

            await self._process_callback(event, ctx, current_state)

        elif isinstance(event, (MessageEvent, BotStartedEvent)):
            await self._process_message(event, ctx, current_state)

    async def _process_message(self, event: BaseEvent, ctx: FSMContext, current_state: Optional[str]) -> None:
        from .compass import handle_message_event
        response_text, keyboard = await handle_message_event(event, ctx, current_state)
        if response_text and event.chat_id:
            await self.transport.send_message(
                chat_id=event.chat_id,
                text=response_text,
                keyboard=keyboard
            )

    async def _process_callback(self, event: CallbackEvent, ctx: FSMContext, current_state: Optional[str]) -> None:
        from .compass import handle_callback_event
        response_text, keyboard = await handle_callback_event(event, ctx, current_state)
        if response_text and event.chat_id:
            await self.transport.send_message(
                chat_id=event.chat_id,
                text=response_text,
                keyboard=keyboard
            )
