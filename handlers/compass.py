import logging
from typing import Any, Dict, List, Optional, Tuple
from transport import BaseEvent, MessageEvent, CallbackEvent, BotStartedEvent
from fsm import FSMContext

logger = logging.getLogger("handlers.compass")


def get_main_menu_keyboard() -> List[List[Dict[str, str]]]:
    return [
        [{"text": "🧭 Социальный Компас", "callback_data": "menu_compass"}],
        [{"text": "ℹ️ О боте MAX", "callback_data": "menu_info"}, {"text": "📋 Помощь", "callback_data": "menu_help"}],
    ]


def get_compass_keyboard() -> List[List[Dict[str, str]]]:
    return [
        [{"text": "💳 Соц. поддержки и льготы", "callback_data": "cat_support"}],
        [{"text": "📅 Мероприятия и досуг", "callback_data": "cat_events"}],
        [{"text": "⚖️ Юридическая помощь", "callback_data": "cat_legal"}],
        [{"text": "🤝 Волонтерство", "callback_data": "cat_volunteer"}],
        [{"text": "⬅️ Назад в меню", "callback_data": "menu_main"}],
    ]


def get_back_keyboard() -> List[List[Dict[str, str]]]:
    return [
        [{"text": "🧭 К категориям", "callback_data": "menu_compass"}, {"text": "🏠 В главное меню", "callback_data": "menu_main"}]
    ]


async def handle_message_event(event: BaseEvent, ctx: FSMContext, current_state: Optional[str]) -> Tuple[str, List[List[Dict[str, str]]]]:
    text = event.text if isinstance(event, MessageEvent) else "/start"
    text = text.strip()

    if text.startswith("/"):
        cmd = text.split()[0].lower()
        args = text[len(cmd):].strip()

        if cmd in ("/start", "/menu"):
            msg = (
                "👋 Добро пожаловать в Демо-Бот «Социальный Компас» для MAX Мессенджера!\n\n"
                "Я ваш цифровой помощник по навигации в социальных сервисах, мероприятиях и поддержке.\n\n"
                "Выберите интересующий вас раздел в меню ниже или введите команду /compass."
            )
            return msg, get_main_menu_keyboard()

        elif cmd == "/compass":
            msg = "🧭 Раздел «Социальный Компас»\n\nВыберите интересующую вас категорию услуг или помощи:"
            return msg, get_compass_keyboard()

        elif cmd == "/help":
            msg = (
                "📋 Справка по командам бота:\n\n"
                "• /start — Главное меню\n"
                "• /compass — Категории социального компаса\n"
                "• /info — Информация о боте и платформе MAX\n"
                "• /echo <текст> — Эхо-команда для проверки\n"
                "• /help — Эта справка"
            )
            return msg, get_main_menu_keyboard()

        elif cmd == "/info":
            msg = (
                "ℹ️ О платформе MAX Messenger & SocialCompas\n\n"
                "• API: MAX Bot API v2 (platform-api2.max.ru)\n"
                "• Хранилище: Redis & MySQL (Docker)\n"
                "• Архитектура: Transport -> FSM -> Dispatcher\n"
                "• Статус: Готов к интеграции схем Miro"
            )
            return msg, get_main_menu_keyboard()

        elif cmd == "/echo":
            if not args:
                return "⚠️ Использование: /echo ваш текст", get_main_menu_keyboard()
            return f"🔊 Эхо: {args}", get_main_menu_keyboard()

    return f"🤖 Вы написали: *{text}*\n\nВоспользуйтесь кнопками ниже для работы с ботом:", get_main_menu_keyboard()


async def handle_callback_event(event: CallbackEvent, ctx: FSMContext, current_state: Optional[str]) -> Tuple[str, List[List[Dict[str, str]]]]:
    data = event.payload

    if data == "menu_compass":
        return "🧭 Раздел «Социальный Компас»\n\nВыберите нужную категорию:", get_compass_keyboard()

    elif data == "cat_support":
        msg = (
            "💳 Социальные выплаты и льготы\n\n"
            "Раздел включает информацию о:\n"
            "- Едином пособии для семей с детьми\n"
            "- Льготах для студентов и пенсионеров\n"
            "- Субсидиях на ЖКХ и проезд"
        )
        return msg, get_back_keyboard()

    elif data == "cat_events":
        msg = (
            "📅 Городские и социальные мероприятия\n\n"
            "Актуальное расписание:\n"
            "1. 🎨 Бесплатный мастер-класс для детей — Завтра, 15:00\n"
            "2. 🏃‍♂️ Забег здоровья и эко-субботник — Суббота, 10:00\n"
            "3. 💻 Курсы цифровой грамотности — Понедельник, 18:00"
        )
        return msg, get_back_keyboard()

    elif data == "cat_legal":
        msg = (
            "⚖️ Бесплатная юридическая помощь\n\n"
            "Консультации юристов по вопросам:\n"
            "- Трудового права\n"
            "- Защиты прав потребителей\n"
            "- Оформления документов и справок"
        )
        return msg, get_back_keyboard()

    elif data == "cat_volunteer":
        msg = (
            "🤝 Волонтерский центр\n\n"
            "Присоединяйтесь к добрым делам!\n"
            "- Помощь пожилым людям\n"
            "- Экологические инициативы\n"
            "- Помощь животным в приютах"
        )
        return msg, get_back_keyboard()

    elif data in ("menu_info", "menu_help"):
        msg = (
            "ℹ️ О платформе MAX Messenger & SocialCompas\n\n"
            "Модульная архитектура: Transport, FSM, Storage (Redis + MySQL).\n"
            "Готов к подключению сценариев Miro!"
        )
        return msg, get_main_menu_keyboard()

    elif data == "menu_main":
        return "🏠 Главное меню SocialCompas\n\nВыберите действие:", get_main_menu_keyboard()

    return f"Вы выбрали: {data}", get_main_menu_keyboard()
