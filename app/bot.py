import asyncio
from aiogram import Bot, Dispatcher
from config import API_TOKEN
from handlers import register_all_handlers

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

async def main():
    register_all_handlers(dp)
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
