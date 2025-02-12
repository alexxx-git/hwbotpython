import aiosqlite

DB_PATH = "data/database.db"

async def db_connect():
    """Создаёт соединение с базой данных."""
    return await aiosqlite.connect(DB_PATH)

async def create_tables():
    """Создаёт таблицы в базе данных."""
    db = await db_connect()  # ✅ Ожидаем выполнение корутины

    async with db:  # ✅ Теперь db поддерживает async with
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS profiles (
                user_id INTEGER PRIMARY KEY,
                weight REAL,
                height REAL,
                age INTEGER,
                activity INTEGER,
                city TEXT,
                goal_calories INTEGER
            );

            CREATE TABLE IF NOT EXISTS water_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                date TEXT DEFAULT (DATE('now'))
            );

            CREATE TABLE IF NOT EXISTS food_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                food_name TEXT,
                calories REAL,
                date TEXT DEFAULT (DATE('now'))
            );

            CREATE TABLE IF NOT EXISTS workout_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                workout_type TEXT,
                workout_time INTEGER,
                calories_burned REAL,
                date TEXT DEFAULT (DATE('now'))
            );
        """)
        await db.commit()  # ✅ Применяем изменения
