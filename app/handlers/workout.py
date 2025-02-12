from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from ..database import db_connect

router = Router()


@router.message(Command("log_workout"))
async def log_workout_cmd(message: Message):
    try:
        _, workout_type, duration = message.text.split()
        duration = int(duration)
        calories_burned = duration * 10  # Примерная формула

        async with db_connect() as db:
            await db.execute(
                "INSERT INTO workout_log (user_id, workout_type, duration, calories_burned) VALUES (?, ?, ?, ?)",
                (message.from_user.id, workout_type, duration, calories_burned))
            await db.commit()

        await message.reply(f"Записана тренировка: {workout_type}, {duration} мин ({calories_burned} ккал).")
    except (IndexError, ValueError):
        await message.reply("Используйте формат: /log_workout <тип тренировки> <время (мин)>")


def register_workout_handlers(dp):
    dp.include_router(router)
