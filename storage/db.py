import json
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
                        discount_info VARCHAR(255) DEFAULT '*Скидки и льготы предоставляются при предоставлении оригинала подтверждающего документа.',
                        address VARCHAR(255) NULL,
                        lat DOUBLE NULL,
                        lng DOUBLE NULL,
                        place_type VARCHAR(64) NULL,
                        promo_text VARCHAR(255) NULL,
                        schedule VARCHAR(128) NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                # Add missing columns if upgrading existing table
                for col_name, col_type in [
                    ("address", "VARCHAR(255) NULL"),
                    ("lat", "DOUBLE NULL"),
                    ("lng", "DOUBLE NULL"),
                    ("place_type", "VARCHAR(64) NULL"),
                    ("promo_text", "VARCHAR(255) NULL"),
                    ("schedule", "VARCHAR(128) NULL"),
                ]:
                    try:
                        await cur.execute(f"ALTER TABLE places ADD COLUMN {col_name} {col_type};")
                    except Exception:
                        pass

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

                # 5. Cities Catalog
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS cities (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(64) NOT NULL UNIQUE,
                        is_active TINYINT(1) DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                # 6. Categories Catalog
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS categories (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(64) NOT NULL UNIQUE,
                        is_active TINYINT(1) DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                # Seed cities & categories if empty
                await cur.execute("INSERT IGNORE INTO cities (name) VALUES ('Москва'), ('Новосибирск'), ('Санкт-Петербург');")
                await cur.execute("INSERT IGNORE INTO categories (name) VALUES ('Студенты'), ('Пенсионеры'), ('Участники СВО');")

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
        # Москва - Студенты
        ("Москва", "Студенты", "Третьяковская галерея", "Главный музей национального искусства России. Шедевры живописи и скульптуры.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Студентам очной формы — скидка 50% по студенческому билету.", "г. Москва, Лаврушинский пер., 10", 55.7415, 37.6208, "Музей", "Скидка 50% студентам очникам", "Вт-Вс: 10:00 - 20:00"),
        ("Москва", "Студенты", "Парк Горького & Музеон", "Главный парковый комплекс столицы с бесплатным Wi-Fi, зонами коворкинга и прокатом.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Вход свободный. Скидки на прокат спортинвентаря по ISIC/студенческому.", "г. Москва, ул. Крымский Вал, 9", 55.7314, 37.6034, "Парк", "Бесплатный вход и зона отдыха", "Круглосуточно"),
        # Москва - Пенсионеры
        ("Москва", "Пенсионеры", "Ботанический сад МГУ «Аптекарский огород»", "Старейший ботанический сад России с уникальными оранжереями и коллекциями цветов.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Бесплатный вход по пенсионному удостоверению по вторникам.", "г. Москва, проспект Мира, 26, стр. 1", 55.7781, 37.6334, "Кафе", "Бесплатный вход по вторникам", "Ежедневно: 10:00 - 20:00"),
        ("Москва", "Пенсионеры", "Музей-заповедник «Царицыно»", "Дворцово-парковый ансамбль Екатерины II с живописными прудами и выставками.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Пенсионерам РФ — льготный билет со скидкой 70%.", "г. Москва, Дольская ул., 1", 55.6146, 37.6845, "Музей", "Льготный билет со скидкой 70%", "Вт-Вс: 06:00 - 00:00"),
        # Москва - Участники СВО
        ("Москва", "Участники СВО", "Музей Победы на Поклонной горе", "Крупнейший военно-исторический музей, посвященный Великой Отечественной войне.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Бесплатный вход для участников СВО и членов их семей.", "г. Москва, пл. Победы, 3", 55.7298, 37.4975, "Музей", "Бесплатное посещение всех выставок", "Вт-Вс: 10:00 - 22:00"),

        # Новосибирск - Студенты
        ("Новосибирск", "Студенты", "Новосибирский зоопарк им. Р.А. Шило", "Один из крупнейших зоопарков России в сосновом бору.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Льготные билеты для студентов высших и средних учебных заведений.", "г. Новосибирск, ул. Тимирязева, 71/1", 55.0537, 82.8837, "Зоопарк", "Скидка 40% по студенческому", "Ежедневно: 09:00 - 19:00"),
        ("Новосибирск", "Студенты", "Театр «Красный факел»", "Ведущий драматический театр Сибири с академическими и современными постановками.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Студенческие билеты со скидкой по Пушкинской карте.", "г. Новосибирск, ул. Ленина, 19", 55.0302, 82.9137, "Кафе", "Скидка по Пушкинской карте", "Вт-Вс: 11:00 - 19:00"),
        # Новосибирск - Пенсионеры
        ("Новосибирск", "Пенсионеры", "Новосибирский театр оперы и балета (НОВАТ)", "Символ города и крупнейший театр России с великим репертуаром.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Специальные льготные программы для пенсионеров.", "г. Новосибирск, Красный проспект, 36", 55.0305, 82.9246, "Кафе", "Льготная билетная программа", "Вт-Вс: 10:00 - 21:00"),
        # Новосибирск - Участники СВО
        ("Новосибирск", "Участники СВО", "Государственная филармония Новосибирска", "Концертный комплекс имени Арнольда Каца.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Бесплатное посещение концертов для участников СВО.", "г. Новосибирск, Красный проспект, 18/1", 55.0239, 82.9248, "Кафе", "Бесплатный вход на концерты", "Ежедневно: 10:00 - 20:00"),

        # Санкт-Петербург - Студенты
        ("Санкт-Петербург", "Студенты", "Государственный Эрмитаж", "Один из величайших музеев мира в Зимнем дворце.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Бесплатное посещение для студентов РФ в определенные дни.", "г. Санкт-Петербург, Дворцовая наб., 34", 59.9398, 30.3146, "Музей", "Бесплатный вход по студенческому", "Вт-Вс: 11:00 - 18:00"),
        ("Санкт-Петербург", "Студенты", "Севкабель Порт", "Культурно-деловое пространство у моря с ярмарками, выставками и катком.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Вход свободный, скидки на мероприятия по студенческому.", "г. Санкт-Петербург, Кожевенная линия, 40", 59.9244, 30.2408, "Спорт", "Свободный вход & скидки на каток", "Ежедневно: 10:00 - 23:00"),
        # Санкт-Петербург - Пенсионеры
        ("Санкт-Петербург", "Пенсионеры", "Русский музей (Михайловский дворец)", "Крупнейший музей российского искусства в Санкт-Петербурге.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Льготный билет для пенсионеров РФ.", "г. Санкт-Петербург, Инженерная ул., 4", 59.9386, 30.3322, "Музей", "Специальная льготная цена", "Ср-Пн: 10:00 - 18:00"),
        # Санкт-Петербург - Участники СВО
        ("Санкт-Петербург", "Участники СВО", "Военно-исторический музей артиллерии", "Один из крупнейших военных музеев мира.", "https://yandex.ru/maps/-/CCUBb4hQ~C", "Бесплатное посещение по удостоверению участника СВО.", "г. Санкт-Петербург, Александровский парк, 7", 59.9538, 30.3142, "Музей", "100% скидка участникам СВО", "Ср-Вс: 11:00 - 18:00"),
    ]

    sql = """
        INSERT INTO places (city, category, title, description, map_url, discount_info, address, lat, lng, place_type, promo_text, schedule)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    await cur.executemany(sql, sample_places)


async def get_db_pool() -> Optional[aiomysql.Pool]:
    """Returns active MySQL connection pool."""
    return _db_pool


# Database helper functions

async def save_user_profile(user_id: str, city: str, category: str):
    """Saves or updates user profile in MySQL. Keeps Bot and MiniApp fully synchronized."""
    pool = await get_db_pool()
    if not pool:
        return
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # 1. Upsert for direct user_id
            await cur.execute(
                """
                INSERT INTO user_profiles (user_id, city, category) VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE city = %s, category = %s, updated_at = CURRENT_TIMESTAMP;
                """,
                (user_id, city, category, city, category),
            )

            # 2. Bidirectional sync:
            # A) If updated from Bot (real user_id), mirror to miniapp_user_1 so MiniApp sees it
            if user_id != "miniapp_user_1" and user_id not in TEST_ACCOUNT_DEFAULTS:
                await cur.execute(
                    """
                    INSERT INTO user_profiles (user_id, city, category) VALUES ('miniapp_user_1', %s, %s)
                    ON DUPLICATE KEY UPDATE city = %s, category = %s, updated_at = CURRENT_TIMESTAMP;
                    """,
                    (city, category, city, category),
                )
            # B) If updated from MiniApp (anonymous miniapp_user_1), mirror to the latest active bot user
            elif user_id == "miniapp_user_1":
                await cur.execute(
                    """
                    SELECT user_id FROM user_profiles
                    WHERE user_id NOT IN ('miniapp_user_1', '998877', '554433', '112233')
                    ORDER BY updated_at DESC LIMIT 1;
                    """
                )
                latest_user = await cur.fetchone()
                if latest_user and latest_user.get("user_id"):
                    latest_uid = latest_user["user_id"]
                    await cur.execute(
                        """
                        UPDATE user_profiles
                        SET city = %s, category = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = %s;
                        """,
                        (city, category, latest_uid),
                    )
                    await cur.execute(
                        """
                        UPDATE user_states
                        SET data = JSON_SET(COALESCE(data, '{}'), '$.city', %s, '$.category', %s)
                        WHERE user_id = %s;
                        """,
                        (city, category, latest_uid),
                    )

            # 3. Sync MySQL user_states table for the direct user_id
            await cur.execute(
                """
                UPDATE user_states
                SET data = JSON_SET(COALESCE(data, '{}'), '$.city', %s, '$.category', %s)
                WHERE user_id = %s;
                """,
                (city, category, user_id),
            )

    # 4. Also directly sync Redis FSM cache so the bot updates instantly without waiting
    try:
        from storage.redis_client import get_redis
        redis_client = await get_redis()
        if redis_client:
            uids_to_sync = [user_id]
            if user_id == "miniapp_user_1":
                keys = await redis_client.keys("fsm:data:*")
                for k in keys:
                    key_str = k.decode("utf-8") if isinstance(k, bytes) else str(k)
                    uids_to_sync.append(key_str.replace("fsm:data:", ""))
            for uid in set(uids_to_sync):
                raw = await redis_client.get(f"fsm:data:{uid}")
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8")
                data = json.loads(raw) if raw else {}
                data["city"] = city
                data["category"] = category
                await redis_client.set(f"fsm:data:{uid}", json.dumps(data, ensure_ascii=False))
                logger.info(f"[fsm.sync] Updated Redis fsm:data:{uid} -> city={city}, category={category}")
    except Exception as e:
        logger.warning(f"Redis FSM sync error: {e}")


TEST_ACCOUNT_DEFAULTS = {
    "998877": {"city": "Москва", "category": "Студенты"},
    "554433": {"city": "Санкт-Петербург", "category": "Пенсионеры"},
    "112233": {"city": "Новосибирск", "category": "Участники СВО"},
}


async def get_user_profile(user_id: str) -> Optional[Dict[str, str]]:
    """
    Fetches user profile from MySQL by user_id.
    Synchronizes between bot user and MiniApp (miniapp_user_1) based on the latest update timestamp.
    """
    # 1. Fixed test accounts check
    if user_id in TEST_ACCOUNT_DEFAULTS:
        pool = await get_db_pool()
        if pool:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(
                        "SELECT city, category FROM user_profiles WHERE user_id = %s;",
                        (user_id,)
                    )
                    row = await cur.fetchone()
                    if row:
                        return row
        return TEST_ACCOUNT_DEFAULTS[user_id]

    pool = await get_db_pool()
    if not pool:
        return {"city": "Москва", "category": "Студенты"}

    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # 2. For real users: check both user_id and miniapp_user_1, taking whichever was updated most recently!
            if user_id and user_id != "miniapp_user_1":
                await cur.execute(
                    """
                    SELECT user_id, city, category, updated_at
                    FROM user_profiles
                    WHERE user_id IN (%s, 'miniapp_user_1')
                    ORDER BY updated_at DESC LIMIT 1;
                    """,
                    (user_id,)
                )
                row = await cur.fetchone()
                if row:
                    # If miniapp_user_1 was the newer one, update the user_id row to keep them in sync
                    if row.get("user_id") == "miniapp_user_1":
                        await cur.execute(
                            """
                            UPDATE user_profiles
                            SET city = %s, category = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE user_id = %s;
                            """,
                            (row["city"], row["category"], user_id),
                        )
                    return {"city": row["city"], "category": row["category"]}

            elif user_id == "miniapp_user_1":
                await cur.execute(
                    "SELECT city, category FROM user_profiles WHERE user_id = 'miniapp_user_1';"
                )
                row = await cur.fetchone()
                if row:
                    return row

            # 3. Default fallback
            return {"city": "Москва", "category": "Студенты"}


async def get_places_by_filter(city: str, category: str) -> List[Dict[str, Any]]:
    """Gets places catalog matching city and category with flexible normalization."""
    pool = await get_db_pool()
    if not pool:
        return []
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            clean_city = city.replace("г.", "").strip()
            clean_cat = category.strip()
            cat_short = clean_cat[:4] if len(clean_cat) >= 4 else clean_cat

            city_pattern = f"%{clean_city}%"
            cat_pattern = f"%{cat_short}%"

            # 1. Primary query matching city and category
            query1 = """
                SELECT * FROM places
                WHERE (city = %s OR city LIKE %s OR %s LIKE CONCAT('%%', city, '%%'))
                  AND (category = %s OR category = 'Все' OR category = 'Все категории' OR category LIKE %s);
            """
            await cur.execute(query1, (city, city_pattern, city, category, cat_pattern))
            rows = await cur.fetchall()
            if rows:
                return rows

            # 2. Fallback query matching city only
            query2 = """
                SELECT * FROM places
                WHERE city = %s OR city LIKE %s OR %s LIKE CONCAT('%%', city, '%%');
            """
            await cur.execute(query2, (city, city_pattern, city))
            rows = await cur.fetchall()
            if rows:
                return rows

            # 3. Universal fallback if DB returns nothing
            await cur.execute("SELECT * FROM places LIMIT 20;")
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
    """Gets user favorite places (only for the specific user)."""
    pool = await get_db_pool()
    if not pool:
        return []
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """
                SELECT p.* FROM places p
                JOIN user_favorites f ON p.id = f.place_id
                WHERE f.user_id = %s
                ORDER BY f.created_at DESC;
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


async def get_all_cities() -> List[Dict[str, Any]]:
    """Fetches all active cities from DB."""
    pool = await get_db_pool()
    if not pool:
        return [
            {"id": 1, "name": "Москва", "is_active": 1},
            {"id": 2, "name": "Новосибирск", "is_active": 1},
            {"id": 3, "name": "Санкт-Петербург", "is_active": 1},
        ]
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT id, name, is_active FROM cities WHERE is_active = 1 ORDER BY id ASC;")
            rows = await cur.fetchall()
            if not rows:
                return [
                    {"id": 1, "name": "Москва", "is_active": 1},
                    {"id": 2, "name": "Новосибирск", "is_active": 1},
                    {"id": 3, "name": "Санкт-Петербург", "is_active": 1},
                ]
            return rows


async def get_all_categories() -> List[Dict[str, Any]]:
    """Fetches all active categories from DB."""
    pool = await get_db_pool()
    if not pool:
        return [
            {"id": 1, "name": "Студенты", "is_active": 1},
            {"id": 2, "name": "Пенсионеры", "is_active": 1},
            {"id": 3, "name": "Участники СВО", "is_active": 1},
        ]
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT id, name, is_active FROM categories WHERE is_active = 1 ORDER BY id ASC;")
            rows = await cur.fetchall()
            if not rows:
                return [
                    {"id": 1, "name": "Студенты", "is_active": 1},
                    {"id": 2, "name": "Пенсионеры", "is_active": 1},
                    {"id": 3, "name": "Участники СВО", "is_active": 1},
                ]
            return rows

