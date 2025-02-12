from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from app.database import db_connect

router = Router()

@router.message(Command("check_progress"))
async def check_progress(message: Message):
    user_id = message.from_user.id
    db = await db_connect()  # ✅ Ждём, пока подключение к БД завершится

    async with db:  # ✅ Теперь можно использовать async with
        async with db.execute("SELECT goal_calories FROM profiles WHERE user_id = ?", (user_id,)) as cursor:
            profile = await cursor.fetchone()

        async with db.execute("SELECT SUM(amount) FROM water_log WHERE user_id = ? AND date = CURRENT_DATE", (user_id,)) as cursor:
            water = await cursor.fetchone()

        async with db.execute("SELECT SUM(calories) FROM food_log WHERE user_id = ? AND date = CURRENT_DATE", (user_id,)) as cursor:
            food = await cursor.fetchone()

        async with db.execute("SELECT SUM(calories_burned) FROM workout_log WHERE user_id = ? AND date = CURRENT_DATE", (user_id,)) as cursor:
            workouts = await cursor.fetchone()

    goal_calories = profile[0] if profile else 2000
    consumed_water = water[0] if water and water[0] else 0
    consumed_calories = food[0] if food and food[0] else 0
    burned_calories = workouts[0] if workouts and workouts[0] else 0
    net_calories = consumed_calories - burned_calories
    remaining_water = max(0, 2400 - consumed_water)

    await message.reply(
        f"📊 *Ваш прогресс на сегодня:*\n"
        f"💧 Вода: {consumed_water} мл / 2400 мл (осталось {remaining_water} мл)\n"
        f"🔥 Калории: {net_calories} ккал / {goal_calories} ккал"
    )

def register_progress_handlers(dp):
    dp.include_router(router)
