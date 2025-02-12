import aiosqlite
from config import DB_NAME
# Подключение к базе данных
async def db_connect():
    return await aiosqlite.connect(DB_NAME)

# Функция для выполнения запроса и выполнения commit
async def execute_query(query, params=()):
    db = await db_connect()  # Подключаемся к базе данных
    try:
        await db.execute(query, params)
        await db.commit()
    finally:
        await db.close()  # Закрываем соединение после выполнения запроса

# Функция для получения данных из базы
async def fetch_one(query, params=()):
    db = await db_connect()  # Подключаемся к базе данных
    try:
        async with db.execute(query, params) as cursor:
            return await cursor.fetchone()
    finally:
        await db.close()  # Закрываем соединение после выполнения запроса

# Пример: создание таблиц
async def create_tables():
    await execute_query('''
    CREATE TABLE IF NOT EXISTS profiles (
        user_id INTEGER PRIMARY KEY,
        weight REAL,
        height REAL,
        age INTEGER,
        activity INTEGER,
        city TEXT,
        goal_calories REAL,
        water_goal REAL DEFAULT 0  
    )
    ''')
    await execute_query('''
    CREATE TABLE IF NOT EXISTS water_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    await execute_query('''
    CREATE TABLE IF NOT EXISTS food_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        food_name TEXT,
        calories REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    await execute_query('''
    CREATE TABLE IF NOT EXISTS workout_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        workout_type TEXT,
        workout_time INTEGER,
        calories_burned REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

# Функция для добавления нового столбца в таблицу (если его ещё нет)
async def add_water_goal_column():
    await execute_query('''
    ALTER TABLE profiles ADD COLUMN water_goal REAL DEFAULT 0
    ''')

# Пример сохранения данных профиля
async def set_profile(user_id, weight, height, age, activity, city, goal_calories):
    # Рассчитываем требуемую норму воды
    water_goal = weight * 30  # Базовая норма воды

    # Добавляем воду за активность
    water_goal += (activity // 30) * 500  # 500 мл за каждые 30 минут активности

    # Учитываем жаркую погоду
    if city and city.lower() in ['moscow', 'hot']:
        water_goal += 1000  # Дополнительно 1000 мл в жаркую погоду
    else:
        water_goal += 500  # Для остальных городов +500 мл

    # Вставляем или обновляем профиль в базе данных, включая рассчитанную норму воды
    await execute_query('''
    INSERT OR REPLACE INTO profiles (user_id, weight, height, age, activity, city, goal_calories, water_goal)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, weight, height, age, activity, city, goal_calories, water_goal))

# Пример получения данных профиля
async def get_profile(user_id):
    db = await db_connect()
    async with db.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)) as cursor:
        result = await cursor.fetchone()
        if result:
            return {
                "weight": result[1],
                "height": result[2],
                "age": result[3],
                "activity": result[4],
                "city": result[5],
                "goal_calories": result[6],
                "water_goal": result[7]
            }
        return None

# Пример логирования воды
async def log_water(user_id, amount):
    db = await db_connect()
    try:
        cursor = await db.execute("SELECT * FROM water_log WHERE user_id = ?", (user_id,))
        existing_log = await cursor.fetchone()

        if existing_log:
            await db.execute("UPDATE water_log SET amount = amount + ? WHERE user_id = ?", (amount, user_id))
        else:
            await db.execute("INSERT INTO water_log (user_id, amount) VALUES (?, ?)", (user_id, amount))

        await db.commit()
    finally:
        await db.close()

# Пример логирования еды
async def log_food(user_id, food_name, calories):
    await execute_query('''
    INSERT INTO food_log (user_id, food_name, calories) VALUES (?, ?, ?)
    ''', (user_id, food_name, calories))

# Пример логирования тренировки
async def log_workout(user_id, workout_type, workout_time, calories_burned):
    await execute_query('''
    INSERT INTO workout_log (user_id, workout_type, workout_time, calories_burned) 
    VALUES (?, ?, ?, ?)
    ''', (user_id, workout_type, workout_time, calories_burned))

# Пример получения прогресса пользователя
async def get_progress(user_id):
    water_consumed_query = 'SELECT SUM(amount) FROM water_log WHERE user_id = ?'
    calories_consumed_query = 'SELECT SUM(calories) FROM food_log WHERE user_id = ?'
    calories_burned_query = 'SELECT SUM(calories_burned) FROM workout_log WHERE user_id = ?'

    water_consumed = await fetch_one(water_consumed_query, (user_id,))
    calories_consumed = await fetch_one(calories_consumed_query, (user_id,))
    calories_burned = await fetch_one(calories_burned_query, (user_id,))

    water_consumed = water_consumed[0] if water_consumed[0] else 0
    calories_consumed = calories_consumed[0] if calories_consumed[0] else 0
    calories_burned = calories_burned[0] if calories_burned[0] else 0

    profile = await get_profile(user_id)
    if profile:
        water_goal = profile['water_goal']  # Используем рассчитанную норму воды

        # Формируем сообщение о прогрессе
        progress_message = (f"Прогресс:\nВода: {water_consumed:.0f} мл из {water_goal:.0f} мл\n"
                            f"Калории: {calories_consumed} ккал из {profile['goal_calories']} ккал\n"
                            f"Сожжено: {calories_burned} ккал\n"
                            f"Балланс: {round(calories_consumed - calories_burned,1)} ккал")
        return progress_message
    return "Профиль не найден."

# Пример получения лога воды
async def get_water_log(user_id):
    db = await db_connect()
    cursor = await db.execute("SELECT amount FROM water_log WHERE user_id = ?", (user_id,))
    result = await cursor.fetchone()
    return result[0] if result else 0  # Если записи нет, возвращаем 0
