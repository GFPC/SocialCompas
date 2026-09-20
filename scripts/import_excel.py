import os
import sys
import openpyxl
import asyncio
import aiomysql

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Add root directory to sys.path
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))
import config

EXCEL_PATH = r"C:\Users\greg\Downloads\БД акции по городам.xlsx"


async def import_excel_data():
    print(f"📦 Импорт данных из Excel: {EXCEL_PATH}")
    wb = openpyxl.load_workbook(EXCEL_PATH)
    sheet = wb.active

    rows = list(sheet.iter_rows(values_only=True))[1:]  # Skip header row

    pool = await aiomysql.create_pool(
        host=config.MYSQL_HOST,
        port=config.MYSQL_PORT,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        db=config.MYSQL_DB,
        autocommit=True,
    )

    imported_count = 0
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # Clear old places data
            await cur.execute("DELETE FROM places;")

            insert_query = """
                INSERT INTO places (city, category, title, place_type, promo_text, schedule, address, map_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """

            for row in rows:
                if not row or not row[0] or not row[2]:
                    continue

                city = str(row[0]).strip()
                category = str(row[1]).strip() if row[1] else "Все"
                title = str(row[2]).strip()
                place_type = str(row[3]).strip() if row[3] else "Место"
                promo_text = str(row[4]).strip() if row[4] else ""
                schedule = str(row[5]).strip() if row[5] else ""
                address = str(row[6]).strip() if row[6] else ""
                map_url = str(row[7]).strip() if row[7] else "https://max.ru"

                await cur.execute(insert_query, (
                    city, category, title, place_type, promo_text, schedule, address, map_url
                ))
                imported_count += 1

    pool.close()
    await pool.wait_closed()
    print(f"🎉 Успешно импортировано {imported_count} записей акций по городам в MySQL!")


if __name__ == "__main__":
    asyncio.run(import_excel_data())
