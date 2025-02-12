from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from app.database import db_connect
from app.states import ProfileForm
from app.utils import calculate_calories, calculate_water_intake, get_temperature

router = Router()

@router.message(Command("set_profile"))
async def cmd_set_profile(message: Message, state: FSMContext):
    await message.reply("Введите ваш вес (в кг):")
    await state.set_state(ProfileForm.weight)

@router.message(ProfileForm.weight)
async def process_weight(message: Message, state: FSMContext):
    weight = float(message.text)
    await state.update_data(weight=weight)
    await message.reply("Введите ваш рост (в см):")
    await state.set_state(ProfileForm.height)

@router.message(ProfileForm.height)
async def process_height(message: Message, state: FSMContext):
    height = float(message.text)
    await state.update_data(height=height)
    await message.reply("Введите ваш возраст:")
    await state.set_state(ProfileForm.age)

@router.message(ProfileForm.age)
async def process_age(message: Message, state: FSMContext):
    age = int(message.text)
    await state.update_data(age=age)
    await message.reply("Сколько минут активности у вас в день?")
    await state.set_state(ProfileForm.activity)

@router.message(ProfileForm.activity)
async def process_activity(message: Message, state: FSMContext):
    activity = int(message.text)
    await state.update_data(activity=activity)
    await message.reply("В каком городе вы находитесь?")
    await state.set_state(ProfileForm.city)

@router.message(ProfileForm.city)
async def process_city(message: Message, state: FSMContext):
    city = message.text if message.text else "Moscow"  # Город по умолчанию
    temp = await get_temperature(city)  # Запрашиваем погоду
    if temp is None:
        city = "Moscow"  # Если город не найден, ставим по умолчанию

    user_data = await state.get_data()
    goal_calories = calculate_calories(user_data['weight'], user_data['height'], user_data['age'], user_data['activity'])
    hot_weather = temp > 25 if temp is not None else False
    water_intake = calculate_water_intake(user_data['weight'], user_data['activity'], hot_weather)

    # Подключение к БД
    db = await db_connect()  # ✅ Ждём подключение
    async with db:  # ✅ Теперь можно использовать async with
        await db.execute("""
            INSERT INTO profiles (user_id, weight, height, age, activity, city, goal_calories)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
            weight=excluded.weight, height=excluded.height, age=excluded.age, 
            activity=excluded.activity, city=excluded.city, goal_calories=excluded.goal_calories
        """, (message.from_user.id, user_data['weight'], user_data['height'], user_data['age'], user_data['activity'], city, goal_calories))
        await db.commit()

    await message.reply(
        f"✅ *Ваш профиль настроен!*\n"
        f"💧 Норма воды: {water_intake} мл\n"
        f"🔥 Норма калорий: {goal_calories} ккал\n"
        f"Используйте /check_progress для отслеживания прогресса."
    )
    await state.clear()
