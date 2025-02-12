from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
import aiohttp
from ..database import db_connect

router = Router()


@router.message(Command("log_food"))
async def log_food_cmd(message: Message):
    food_name = " ".join(message.text.split()[1:])
    if not food_name:
        await message.reply("Используйте формат: /log_food <название продукта>")
        return

    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://world.openfoodfacts.org/api/v0/product/{food_name}.json") as resp:
            data = await resp.json()
            if "product" in data:
                calories = data["product"]["nutriments"]["energy-kcal_100g"]
                await message.reply(f"{food_name} содержит {calories} ккал на 100г. Сколько грамм вы съели?")

                async with db_connect() as db:
                    await db.execute("INSERT INTO food_log (user_id, food_name, calories) VALUES (?, ?, ?)",
                                     (message.from_user.id, food_name, calories))
                    await db.commit()
            else:
                await message.reply("Не удалось найти информацию о продукте.")


def register_food_handlers(dp):
    dp.include_router(router)
