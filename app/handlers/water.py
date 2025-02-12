from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from ..database import db_connect

router = Router()


@router.message(Command("log_water"))
async def log_water_cmd(message: Message):
    try:
        amount = float(message.text.split()[1])
        async with db_connect() as db:
            await db.execute("INSERT INTO water_log (user_id, amount) VALUES (?, ?)", (message.from_user.id, amount))
            await db.commit()

        await message.reply(f"Записано {amount} мл воды.")
    except (IndexError, ValueError):
        await message.reply("Используйте формат: /log_water <количество>")


def register_water_handlers(dp):
    dp.include_router(router)
