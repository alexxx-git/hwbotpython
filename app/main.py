from aiogram import Bot, Dispatcher
import asyncio
from app.handlers import register_handlers
from config import API_TOKEN

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

register_handlers(dp)

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
