import logging
from typing import Any, Dict, Optional, Tuple
from max_api import build_keyboard, MaxBotAPI

logger = logging.getLogger("handlers")


class BotHandlers:
    """
    Business logic and message handlers for SocialCompas MAX Demo Bot.
    """

    def __init__(self, api: Optional[MaxBotAPI] = None):
        self.api = api or MaxBotAPI()

    async def handle_update(self, update: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, Any]]]:
        """
        Processes an incoming update dict (message or callback query).
        Returns a tuple: (chat_id, response_text, keyboard_markup)
        """
        # Handle inline callback query (button press)
        if "callback_query" in update:
            cb = update["callback_query"]
            chat_id = str(cb.get("message", {}).get("chat", {}).get("id") or cb.get("from", {}).get("id"))
            data = cb.get("data", "")
            return await self.handle_callback(chat_id, data)

        # Handle standard message
        message = update.get("message", update)
        chat_id = str(message.get("chat", {}).get("id") or message.get("from", {}).get("id", "default_chat"))
        text = message.get("text", "").strip()

        if not text:
            return chat_id, "💬 Извините, я принимаю текстовые сообщения и команды.", self.get_main_menu_keyboard()

        # Command routing
        if text.startswith("/"):
            cmd = text.split()[0].lower()
            args = text[len(cmd):].strip()
            return await self.handle_command(chat_id, cmd, args)

        # Non-command message handling
        return chat_id, f"🤖 Вы написали: *{text}*\n\nВоспользуйтесь кнопками ниже для работы с бота-помощником:", self.get_main_menu_keyboard()

    async def handle_command(self, chat_id: str, command: str, args: str) -> Tuple[str, str, Dict[str, Any]]:
        """Handles slash commands."""
        if command in ("/start", "/menu"):
            text = (
                "👋 **Добро пожаловать в Демо-Бот «Социальный Компас» для MAX Мессенджера!**\n\n"
                "Я ваш цифровой помощник по навигации в социальных сервисах, мероприятиях и поддержке.\n\n"
                "Выберите интересующий вас раздел в меню ниже или введите команду `/compass`."
            )
            return chat_id, text, self.get_main_menu_keyboard()

        elif command == "/compass":
            text = (
                "🧭 **Раздел «Социальный Компас»**\n\n"
                "Выберите интересующую вас категорию услуг или помощи:"
            )
            return chat_id, text, self.get_compass_keyboard()

        elif command == "/help":
            text = (
                "📋 **Справка по командам бота:**\n\n"
                "• `/start` — Главное меню\n"
                "• `/compass` — Категории социального компаса\n"
                "• `/info` — Информация о боте и платформе MAX\n"
                "• `/echo <текст>` — Эхо-команда для проверки\n"
                "• `/help` — Эта справка"
            )
            return chat_id, text, self.get_main_menu_keyboard()

        elif command == "/info":
            text = (
                "ℹ️ **О платформе MAX Messenger & SocialCompas**\n\n"
                "• **API:** MAX Bot API v2 (`https://platform-api2.max.ru`)\n"
                "• **Авторизация:** Bearer токен от @MasterBot / business.max.ru\n"
                "• **Статус:** Демонстрационный бот готов к интеграции\n"
                "• **Версия:** 1.0.0 (SocialCompas Demo)"
            )
            return chat_id, text, self.get_info_keyboard()

        elif command == "/echo":
            if not args:
                return chat_id, "⚠️ Использование: `/echo ваш текст`", self.get_main_menu_keyboard()
            return chat_id, f"🔊 **Эхо:** {args}", self.get_main_menu_keyboard()

        else:
            return chat_id, f"❓ Неизвестная команда `{command}`. Используйте `/help` для просмотра списка команд.", self.get_main_menu_keyboard()

    async def handle_callback(self, chat_id: str, data: str) -> Tuple[str, str, Dict[str, Any]]:
        """Handles inline keyboard button callbacks."""
        if data == "menu_compass":
            text = "🧭 **Раздел «Социальный Компас»**\n\nВыберите нужную категорию:"
            return chat_id, text, self.get_compass_keyboard()

        elif data == "cat_support":
            text = (
                "💳 **Социальные выплаты и льготы**\n\n"
                "Раздел включает информацию о:\n"
                "- Едином пособии для семей с детьми\n"
                "- Льготах для студентов и пенсионеров\n"
                "- Субсидиях на ЖКХ и проезд\n\n"
                "Для уточнения выберите категорию или подайте заявку."
            )
            return chat_id, text, self.get_back_keyboard()

        elif data == "cat_events":
            text = (
                "📅 **Городские и социальные мероприятия**\n\n"
                "Актуальное расписание:\n"
                "1. 🎨 Бесплатный мастер-класс для детей — Завтра, 15:00\n"
                "2. 🏃‍♂️ Забег здоровья и эко-субботник — Суббота, 10:00\n"
                "3. 💻 Курсы цифровой грамотности — Понедельник, 18:00"
            )
            return chat_id, text, self.get_back_keyboard()

        elif data == "cat_legal":
            text = (
                "⚖️ **Бесплатная юридическая помощь**\n\n"
                "Консультации юристов по вопросам:\n"
                "- Трудового права\n"
                "- Защиты прав потребителей\n"
                "- Оформления документов и справок"
            )
            return chat_id, text, self.get_back_keyboard()

        elif data == "cat_volunteer":
            text = (
                "🤝 **Волонтерский центр**\n\n"
                "Присоединяйтесь к добрым делам!\n"
                "- Помощь пожилым людям\n"
                "- Экологические инициативы\n"
                "- Помощь животным в приютах"
            )
            return chat_id, text, self.get_back_keyboard()

        elif data == "menu_info":
            text = (
                "ℹ️ **Информация о MAX Bot API**\n\n"
                "Интеграция бота выполнена с использованием обновленных стандартов MAX Bot API v2.\n"
                "Бот поддерживает Webhook, Long-Polling и интерактивные кнопки."
            )
            return chat_id, text, self.get_info_keyboard()

        elif data == "menu_main":
            text = "🏠 **Главное меню SocialCompas**\n\nВыберите действие:"
            return chat_id, text, self.get_main_menu_keyboard()

        else:
            return chat_id, f"Вы выбрали: *{data}*", self.get_main_menu_keyboard()

    # --- Keyboard Layout Helpers ---

    def get_main_menu_keyboard(self) -> Dict[str, Any]:
        return build_keyboard([
            [{"text": "🧭 Социальный Компас", "callback_data": "menu_compass"}],
            [{"text": "ℹ️ О боте MAX", "callback_data": "menu_info"}, {"text": "📋 Помощь", "callback_data": "menu_help"}],
        ])

    def get_compass_keyboard(self) -> Dict[str, Any]:
        return build_keyboard([
            [{"text": "💳 Соц. поддержки и льготы", "callback_data": "cat_support"}],
            [{"text": "📅 Мероприятия и досуг", "callback_data": "cat_events"}],
            [{"text": "⚖️ Юридическая помощь", "callback_data": "cat_legal"}],
            [{"text": "🤝 Волонтерство", "callback_data": "cat_volunteer"}],
            [{"text": "⬅️ Назад в меню", "callback_data": "menu_main"}],
        ])

    def get_back_keyboard(self) -> Dict[str, Any]:
        return build_keyboard([
            [{"text": "🧭 К категориям", "callback_data": "menu_compass"}, {"text": "🏠 В главное меню", "callback_data": "menu_main"}]
        ])

    def get_info_keyboard(self) -> Dict[str, Any]:
        return build_keyboard([
            [{"text": "🏠 Главное меню", "callback_data": "menu_main"}]
        ])
