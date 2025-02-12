from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply("Привет! Используйте /set_profile для настройки профиля.")

def register_misc_handlers(dp):
    dp.include_router(router)
