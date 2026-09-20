import logging
import aiomysql
from typing import Any, Dict, List, Optional

import config

logger = logging.getLogger("storage.db")
_db_pool: Optional[aiomysql.Pool] = None


async def init_db():
    """
    Initializes MySQL connection pool and creates required schema & tables.
    """
    global _db_pool
    try:
        _db_pool = await aiomysql.create_pool(
            host=config.MYSQL_HOST,
            port=config.MYSQL_PORT,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            db=config.MYSQL_DB,
            autocommit=True,
            maxsize=10,
        )
        logger.info(f"Connected to MySQL database '{config.MYSQL_DB}' at {config.MYSQL_HOST}:{config.MYSQL_PORT}")

        async with _db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 1. FSM User States
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_states (
                        user_id VARCHAR(64) PRIMARY KEY,
                        state VARCHAR(128) NULL,
                        data JSON NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                # 2. User Profiles (City & Category from Onboarding)
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_profiles (
                        user_id VARCHAR(64) PRIMARY KEY,
                        city VARCHAR(64) NOT NULL,
                        category VARCHAR(64) NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                # 3. Places Catalog
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS places (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        city VARCHAR(64) NOT NULL,
                        category VARCHAR(64) NOT NULL,
                        title VARCHAR(255) NOT NULL,
                        description TEXT NOT NULL,
                        map_url VARCHAR(255) NOT NULL,
                        discount_info VARCHAR(255) DEFAULT '*Скидки и льготы предоставляются при предоставлении оригинала подтверждающего документа.'
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                # 4. User Favorites
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_favorites (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id VARCHAR(64) NOT NULL,
                        place_id INT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE KEY unique_user_place (user_id, place_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                # Seed initial places data if empty
                await cur.execute("SELECT COUNT(*) FROM places;")
                count = (await cur.fetchone())[0]
                if count == 0:
                    await _seed_places(cur)

        logger.info("MySQL tables & initial seed initialized successfully.")
    except Exception as exc:
        logger.warning(f"Could not connect to MySQL: {exc}")
        _db_pool = None


async def _seed_places(cur):
    sample_places = [
        # Москва - Студент
        ("Москва", "Студент", "Третьяковская галерея", "Главный музей национального искусства России. Шедевры живописи и скульптуры.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Студентам очной формы — скидка 50% по студенческому билету."),
        ("Москва", "Студент", "Парк Горького & Музеон", "Главный парковый комплекс столицы с бесплатным Wi-Fi, зонами коворкинга и прокатом.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Вход свободный. Скидки на прокат спортинвентаря по ISIC/студенческому."),
        # Москва - Пенсионер
        ("Москва", "Пенсионер", "Ботанический сад МГУ «Аптекарский огород»", "Старейший ботанический сад России с уникальными оранжереями и коллекциями цветов.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Бесплатный вход по пенсионному удостоверению по вторникам."),
        ("Москва", "Пенсионер", "Музей-заповедник «Царицыно»", "Дворцово-парковый ансамбль Екатерины II с живописными прудами и выставками.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Пенсионерам РФ — льготный билет со скидкой 70%."),
        # Москва - Участник СВО
        ("Москва", "Участник СВО", "Музей Победы на Поклонной горе", "Крупнейший военно-исторический музей, посвященный Великой Отечественной войне.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Бесплатный вход для участников СВО и членов их семей."),

        # Новосибирск - Студент
        ("Новосибирск", "Студент", "Новосибирский зоопарк им. Р.А. Шило", "Один из крупнейших зоопарков России в сосновом бору.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Льготные билеты для студентов высших и средних учебных заведений."),
        ("Новосибирск", "Студент", "Театр «Красный факел»", "Ведущий драматический театр Сибири с академическими и современными постановками.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Студенческие билеты со скидкой по Пушкинской карте."),
        # Новосибирск - Пенсионер
        ("Новосибирск", "Пенсионер", "Новосибирский театр оперы и балета (НОВАТ)", "Символ города и крупнейший театр России с великим репертуаром.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Специальные льготные программы для пенсионеров."),
        # Новосибирск - Участник СВО
        ("Новосибирск", "Участник СВО", "Государственная филармония Новосибирска", "Концертный комплекс имени Арнольда Каца.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Бесплатное посещение концертов для участников СВО."),

        # Санкт-Петербург - Студент
        ("Санкт-Петербург", "Студент", "Государственный Эрмитаж", "Один из величайших музеев мира в Зимнем дворце.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Бесплатное посещение для студентов РФ в определенные дни."),
        ("Санкт-Петербург", "Студент", "Севкабель Порт", "Культурно-деловое пространство у моря с ярмарками, выставками и катом.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Вход свободный, скидки на мероприятия по студенческому."),
        # Санкт-Петербург - Пенсионер
        ("Санкт-Петербург", "Пенсионер", "Русский музей (Михайловский дворец)", "Крупнейший музей российского искусства в Санкт-Петербурге.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Льготный билет для пенсионеров РФ."),
        # Санкт-Петербург - Участник СВО
        ("Санкт-Петербург", "Участник СВО", "Военно-исторический музей артиллерии", "Один из крупнейших военных музеев мира.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Бесплатное посещение по удостоверению участника СВО."),
    ]

    sql = """
        INSERT INTO places (city, category, title, description, map_url, discount_info)
        VALUES (%s, %s, %s, %s, %s, %s);
    """
    await cur.executemany(sql, sample_places)


async def get_db_pool() -> Optional[aiomysql.Pool]:
    """Returns active MySQL connection pool."""
    return _db_pool


# Database helper functions

async def save_user_profile(user_id: str, city: str, category: str):
    """Saves or updates user profile in MySQL."""
    pool = await get_db_pool()
    if not pool:
        return
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO user_profiles (user_id, city, category) VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE city = %s, category = %s;
                """,
                (user_id, city, category, city, category),
            )


async def get_user_profile(user_id: str) -> Optional[Dict[str, str]]:
    """Fetches user profile from MySQL."""
    pool = await get_db_pool()
    if not pool:
        return None
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT city, category FROM user_profiles WHERE user_id = %s;", (user_id,))
            return await cur.fetchone()


async def get_places_by_filter(city: str, category: str) -> List[Dict[str, Any]]:
    """Gets places catalog matching city and category."""
    pool = await get_db_pool()
    if not pool:
        return []
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM places WHERE city = %s AND category = %s;", (city, category))
            return await cur.fetchall()


async def get_place_by_id(place_id: int) -> Optional[Dict[str, Any]]:
    """Gets place detail by ID."""
    pool = await get_db_pool()
    if not pool:
        return None
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM places WHERE id = %s;", (place_id,))
            return await cur.fetchone()


async def add_favorite(user_id: str, place_id: int):
    """Adds a place to user favorites."""
    pool = await get_db_pool()
    if not pool:
        return
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT IGNORE INTO user_favorites (user_id, place_id) VALUES (%s, %s);",
                (user_id, place_id),
            )


async def remove_favorite(user_id: str, place_id: int):
    """Removes a place from user favorites."""
    pool = await get_db_pool()
    if not pool:
        return
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM user_favorites WHERE user_id = %s AND place_id = %s;",
                (user_id, place_id),
            )


async def get_user_favorites(user_id: str) -> List[Dict[str, Any]]:
    """Gets user favorite places."""
    pool = await get_db_pool()
    if not pool:
        return []
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """
                SELECT p.* FROM places p
                JOIN user_favorites f ON p.id = f.place_id
                WHERE f.user_id = %s;
                """,
                (user_id,),
            )
            return await cur.fetchall()


async def is_favorite(user_id: str, place_id: int) -> bool:
    """Checks if place is in user favorites."""
    pool = await get_db_pool()
    if not pool:
        return False
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT 1 FROM user_favorites WHERE user_id = %s AND place_id = %s;",
                (user_id, place_id),
            )
            row = await cur.fetchone()
            return row is not None
