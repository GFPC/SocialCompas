import logging
from typing import Any, Dict, List, Optional, Tuple

from transport import BaseEvent, MessageEvent, CallbackEvent, BotStartedEvent
from fsm import FSMContext
from fsm.state import SocialCompasSG
from storage.db import (
    save_user_profile,
    get_user_profile,
    get_places_by_filter,
    get_place_by_id,
    add_favorite,
    remove_favorite,
    get_user_favorites,
    is_favorite,
)

logger = logging.getLogger("handlers.compass")


# --- Keyboard Helpers ---

def get_city_keyboard() -> List[List[Dict[str, str]]]:
    return [
        [{"text": "🏙 Москва", "callback_data": "city_Москва"}],
        [{"text": "🌲 Новосибирск", "callback_data": "city_Новосибирск"}],
        [{"text": "🏛 Санкт-Петербург", "callback_data": "city_Санкт-Петербург"}],
    ]


def get_category_keyboard() -> List[List[Dict[str, str]]]:
    return [
        [{"text": "👴 Пенсионер", "callback_data": "cat_Пенсионер"}],
        [{"text": "🎓 Студент", "callback_data": "cat_Студент"}],
        [{"text": "🪖 Участник СВО", "callback_data": "cat_Участник СВО"}],
    ]


def get_main_menu_keyboard() -> List[List[Dict[str, str]]]:
    return [
        [{"text": "📍 Список мест", "callback_data": "view_places"}],
        [{"text": "⭐ Избранное", "callback_data": "view_favorites"}],
        [{"text": "📱 Перейти в мини приложение", "url": "https://max.ru"}],
        [{"text": "⚙️ Настройки", "callback_data": "view_settings"}],
    ]


def get_settings_keyboard() -> List[List[Dict[str, str]]]:
    return [
        [{"text": "✏️ Изменить данные", "callback_data": "edit_profile"}],
        [{"text": "🏠 В главное меню", "callback_data": "menu_main"}],
    ]


def get_places_list_keyboard(places: List[Dict[str, Any]]) -> List[List[Dict[str, str]]]:
    keyboard = []
    for place in places:
        keyboard.append([{"text": f"🏛 {place['title']}", "callback_data": f"place_{place['id']}"}])
    keyboard.append([{"text": "🏠 В главное меню", "callback_data": "menu_main"}])
    return keyboard


def get_place_detail_keyboard(place_id: int, is_fav: bool, map_url: str) -> List[List[Dict[str, str]]]:
    fav_btn_text = "❌ Удалить из избранного" if is_fav else "⭐ Добавить в избранное"
    fav_cb = f"rem_fav_{place_id}" if is_fav else f"add_fav_{place_id}"

    return [
        [{"text": fav_btn_text, "callback_data": fav_cb}],
        [{"text": "🗺 Посмотреть на карте", "url": map_url}],
        [{"text": "🔙 К списку мест", "callback_data": "view_places"}],
        [{"text": "🏠 Вернуться на главную", "callback_data": "menu_main"}],
    ]


# --- Event Handling ---

async def handle_message_event(event: BaseEvent, ctx: FSMContext, current_state: Optional[str]) -> Tuple[str, List[List[Dict[str, str]]]]:
    text = event.text if isinstance(event, MessageEvent) else "/start"
    text = text.strip()

    # /start command triggers onboarding survey
    if text.startswith("/") or not current_state:
        cmd = text.split()[0].lower() if text.startswith("/") else "/start"

        if cmd in ("/start", "/menu"):
            await ctx.set_state(SocialCompasSG.SELECT_CITY)
            msg = (
                "👋 Добро пожаловать в чат-бот «Социальный компас».\n\n"
                "Для того, чтобы я мог помочь вам найти подходящие места, пройдите небольшой опрос.\n\n"
                "Выберите ваш город:"
            )
            return msg, get_city_keyboard()

    # Default fallback
    data = await ctx.get_data()
    city = data.get("city", "Москва")
    category = data.get("category", "Студент")
    msg = f"🤖 Ваш профиль: {city} ({category}). Воспользуйтесь меню для поиска мест:"
    return msg, get_main_menu_keyboard()


async def handle_callback_event(event: CallbackEvent, ctx: FSMContext, current_state: Optional[str]) -> Tuple[str, List[List[Dict[str, str]]]]:
    data = event.payload
    user_id = event.user_id

    # 1. City selection step
    if data.startswith("city_"):
        selected_city = data.replace("city_", "")
        await ctx.update_data(city=selected_city)
        await ctx.set_state(SocialCompasSG.SELECT_CATEGORY)
        msg = f"Вы выбрали: *{selected_city}*\n\nТеперь выберите вашу категорию:"
        return msg, get_category_keyboard()

    # 2. Category selection step
    if data.startswith("cat_"):
        selected_cat = data.replace("cat_", "")
        user_data = await ctx.update_data(category=selected_cat)
        city = user_data.get("city", "Москва")

        # Save to MySQL persistence
        await save_user_profile(user_id, city, selected_cat)
        await ctx.set_state(SocialCompasSG.MAIN_MENU)

        msg = (
            "Благодарю за ответы! Вы сможете изменить их позже в настройках.\n"
            "Интересные места уже ждут вас."
        )
        return msg, get_main_menu_keyboard()

    # 3. Main menu navigation
    if data == "menu_main":
        await ctx.set_state(SocialCompasSG.MAIN_MENU)
        return "🏠 Главное меню Социального Компаса:", get_main_menu_keyboard()

    # 4. View Places List
    if data == "view_places":
        profile = await get_user_profile(user_id)
        fsm_data = await ctx.get_data()
        city = profile["city"] if profile else fsm_data.get("city", "Москва")
        category = profile["category"] if profile else fsm_data.get("category", "Студент")

        places = await get_places_by_filter(city, category)
        await ctx.set_state(SocialCompasSG.PLACES_LIST)

        if not places:
            msg = f"📍 В городе *{city}* для категории *{category}* места пока не найдены."
            return msg, get_main_menu_keyboard()

        msg = f"📍 *Список мест в г. {city} ({category})*:\n\nВыберите место, которое планируете посетить:"
        return msg, get_places_list_keyboard(places)

    # 5. View Place Detail
    if data.startswith("place_"):
        try:
            place_id = int(data.replace("place_", ""))
            place = await get_place_by_id(place_id)
            if not place:
                return "⚠️ Место не найдено.", get_main_menu_keyboard()

            await ctx.set_state(SocialCompasSG.PLACE_DETAIL)
            is_fav = await is_favorite(user_id, place_id)

            msg = (
                f"🏛 *{place['title']}*\n\n"
                f"{place['description']}\n\n"
                f"ℹ️ {place['discount_info']}\n\n"
                f"_{place['discount_info']}_"
            )
            return msg, get_place_detail_keyboard(place_id, is_fav, place["map_url"])
        except ValueError:
            pass

    # 6. Add/Remove Favorites
    if data.startswith("add_fav_"):
        place_id = int(data.replace("add_fav_", ""))
        await add_favorite(user_id, place_id)
        place = await get_place_by_id(place_id)
        msg = f"✅ Место *{place['title'] if place else ''}* добавлено в избранное!"
        return msg, get_place_detail_keyboard(place_id, True, place["map_url"] if place else "#")

    if data.startswith("rem_fav_"):
        place_id = int(data.replace("rem_fav_", ""))
        await remove_favorite(user_id, place_id)
        place = await get_place_by_id(place_id)
        msg = f"❌ Место *{place['title'] if place else ''}* удалено из избранного."
        return msg, get_place_detail_keyboard(place_id, False, place["map_url"] if place else "#")

    # 7. View Favorites List
    if data == "view_favorites":
        await ctx.set_state(SocialCompasSG.FAVORITES)
        favs = await get_user_favorites(user_id)

        if not favs:
            msg = "⭐ *Ваши сохраненные места*\n\nУ вас пока нет добавленных мест в избранное."
            return msg, get_main_menu_keyboard()

        msg = "⭐ *Ваши сохраненные места*:\n\nВыберите место для просмотра:"
        return msg, get_places_list_keyboard(favs)

    # 8. Settings Screen
    if data == "view_settings":
        await ctx.set_state(SocialCompasSG.SETTINGS)
        profile = await get_user_profile(user_id)
        fsm_data = await ctx.get_data()
        city = profile["city"] if profile else fsm_data.get("city", "Не выбран")
        category = profile["category"] if profile else fsm_data.get("category", "Не выбрана")

        msg = (
            "⚙️ *Настройки профиля*\n\n"
            f"• Ваш город: *{city}*\n"
            f"• Категория: *{category}*\n\n"
            "Вы можете изменить данные в боте или в мини-приложении."
        )
        return msg, get_settings_keyboard()

    # 9. Edit Data (Re-run survey)
    if data == "edit_profile":
        await ctx.set_state(SocialCompasSG.SELECT_CITY)
        msg = "✏️ *Изменение профиля*\n\nВыберите ваш новый город:"
        return msg, get_city_keyboard()

    return "Выберите действие из меню:", get_main_menu_keyboard()
