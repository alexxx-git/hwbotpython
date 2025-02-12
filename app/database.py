import aiosqlite

# Подключение к базе данных
DB_NAME = "bot_database.db"


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
        goal_calories REAL
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


# Пример сохранения данных профиля
async def set_profile(user_id, weight, height, age, activity, city, goal_calories):
    await execute_query('''
    INSERT OR REPLACE INTO profiles (user_id, weight, height, age, activity, city, goal_calories)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, weight, height, age, activity, city, goal_calories))


# Пример получения данных профиля
async def get_profile(user_id):
    return await fetch_one('''
    SELECT * FROM profiles WHERE user_id = ?
    ''', (user_id,))


# Пример логирования воды
async def log_water(user_id, amount):
    async with aiosqlite.connect('database.db') as db:
        # Проверяем, есть ли уже запись для этого пользователя
        cursor = await db.execute("SELECT * FROM water_log WHERE user_id = ?", (user_id,))
        existing_log = await cursor.fetchone()

        if existing_log:
            # Обновляем запись
            await db.execute("UPDATE water_log SET amount = amount + ? WHERE user_id = ?", (amount, user_id))
        else:
            # Создаем новую запись
            await db.execute("INSERT INTO water_log (user_id, amount) VALUES (?, ?)", (user_id, amount))

        await db.commit()


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

    # Если записи о воде/едах/тренировках нет, то возвращаем 0
    water_consumed = water_consumed[0] if water_consumed[0] else 0
    calories_consumed = calories_consumed[0] if calories_consumed[0] else 0
    calories_burned = calories_burned[0] if calories_burned[0] else 0

    profile = await get_profile(user_id)
    if profile:
        water_goal = profile[1] * 30 + (profile[4] / 30) * 500 + (
            1000 if profile[5] and profile[5].lower() in ['moscow', 'hot'] else 500)
        progress_message = f"Прогресс:\nВода: {water_consumed:.0f} мл из {water_goal:.0f} мл\nКалории: {calories_consumed} ккал из {profile[6]} ккал\nСожжено: {calories_burned} ккал"
        return progress_message
    return "Профиль не найден."

async def get_profile(user_id):
    async with aiosqlite.connect('database.db') as db:
        cursor = await db.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
        result = await cursor.fetchone()
        if result:
            return {
                "weight": result[1],
                "height": result[2],
                "age": result[3],
                "activity": result[4],
                "city": result[5],
                "goal_calories": result[6]
            }
        return None


async def get_water_log(user_id):
    async with aiosqlite.connect('database.db') as db:
        cursor = await db.execute("SELECT amount FROM water_log WHERE user_id = ?", (user_id,))
        result = await cursor.fetchone()
        return result[0] if result else 0  # Если записи нет, возвращаем 0
