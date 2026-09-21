import os
import sys
import openpyxl
import asyncio
import aiomysql

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Add root directory to sys.path
BASE_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
import config

EXCEL_FILES = [
    os.path.join(BASE_DIR, "data", "БД акции по городам.xlsx"),
    os.path.join(BASE_DIR, "data", "Санкт-Петербург.xlsx"),
    r"C:\Users\greg\Downloads\БД акции по городам.xlsx",
    r"C:\Users\greg\Downloads\Санкт-Петербург.xlsx",
]


async def import_excel_data():
    pool = await aiomysql.create_pool(
        host=config.MYSQL_HOST,
        port=config.MYSQL_PORT,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        db=config.MYSQL_DB,
        autocommit=True,
    )

    total_imported = 0
    processed_paths = set()

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # Clear old places data
            await cur.execute("DELETE FROM places;")

            insert_query = """
                INSERT INTO places (city, category, title, place_type, promo_text, schedule, address, map_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """

            for file_path in EXCEL_FILES:
                if not os.path.exists(file_path):
                    continue

                filename = os.path.basename(file_path)
                if filename in processed_paths:
                    continue
                processed_paths.add(filename)

                print(f"📦 Импорт данных из Excel: {file_path}")
                wb = openpyxl.load_workbook(file_path)
                sheet = wb.active
                rows = list(sheet.iter_rows(values_only=True))[1:]

                file_count = 0
                for row in rows:
                    if not row or not row[0] or not row[2]:
                        continue

                    city = str(row[0]).strip()
                    category = str(row[1]).strip() if row[1] else "Все"
                    title = str(row[2]).strip()
                    place_type = str(row[3]).strip() if len(row) > 3 and row[3] else "Место"
                    promo_text = str(row[4]).strip() if len(row) > 4 and row[4] else ""
                    schedule = str(row[5]).strip() if len(row) > 5 and row[5] else ""
                    address = str(row[6]).strip() if len(row) > 6 and row[6] else ""
                    map_url = str(row[7]).strip() if len(row) > 7 and row[7] else "https://max.ru"

                    await cur.execute(insert_query, (
                        city, category, title, place_type, promo_text, schedule, address, map_url
                    ))
                    file_count += 1

                total_imported += file_count
                print(f"  -> Добавлено {file_count} записей из {filename}")

    pool.close()
    await pool.wait_closed()
    print(f"\n🎉 Всего успешно импортировано {total_imported} записей мест и акций в MySQL!")


if __name__ == "__main__":
    asyncio.run(import_excel_data())
