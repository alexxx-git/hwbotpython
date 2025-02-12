import asyncio
import aiohttp
import aiosqlite
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import create_tables
from database import get_profile, get_water_log
from config import API_TOKEN
from utils import calculate_water_intake, calculate_calories, get_temperature, get_calories
from database import set_profile, get_progress, log_water, log_food, log_workout
bot = Bot(token=API_TOKEN)
dp = Dispatcher()


class ProfileForm(StatesGroup):
    weight = State()
    height = State()
    age = State()
    activity = State()
    city = State()
    goal_calories = State()
# Определяем состояния
class FoodState(StatesGroup):
    waiting_for_calories = State()
    waiting_for_grams = State()



@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply("Привет! Я помогу вам следить за нормой воды и калорий. Начните с /set_profile.")


@dp.message(Command("set_profile"))
async def cmd_set_profile(message: Message, state: FSMContext):
    await message.reply("Введите ваш вес (в кг):")
    await state.set_state(ProfileForm.weight)  # Переходим к состоянию 'weight'


@dp.message(ProfileForm.weight)
async def process_weight(message: Message, state: FSMContext):
    weight = float(message.text)
    await state.update_data(weight=weight)
    await message.reply("Введите ваш рост (в см):")
    await state.set_state(ProfileForm.height)  # Переходим к состоянию 'height'


@dp.message(ProfileForm.height)
async def process_height(message: Message, state: FSMContext):
    height = float(message.text)
    await state.update_data(height=height)
    await message.reply("Введите ваш возраст:")
    await state.set_state(ProfileForm.age)  # Переходим к состоянию 'age'


@dp.message(ProfileForm.age)
async def process_age(message: Message, state: FSMContext):
    age = int(message.text)
    await state.update_data(age=age)
    await message.reply("Сколько минут активности у вас в день?")
    await state.set_state(ProfileForm.activity)  # Переходим к состоянию 'activity'


@dp.message(ProfileForm.activity)
async def process_activity(message: Message, state: FSMContext):
    activity = int(message.text)
    await state.update_data(activity=activity)
    await message.reply("В каком городе вы находитесь?")
    await state.set_state(ProfileForm.city)  # Переходим к состоянию 'city'


@dp.message(ProfileForm.city)
async def process_city(message: Message, state: FSMContext):
    city = message.text.strip()  # Убираем пробелы
    if not city:
        city = "Moscow"  # Если пользователь не ввел город, устанавливаем значение по умолчанию

    user_data = await state.get_data()
    goal_calories = calculate_calories(user_data['weight'], user_data['height'], user_data['age'],
                                       user_data['activity'])

    # Получаем температуру для города
    temp = await get_temperature(city)  # Переходим к асинхронному вызову получения температуры
    hot_weather = temp > 25

    # Рассчитываем норму воды с учетом температуры
    water_intake = calculate_water_intake(user_data['weight'], user_data['activity'], hot_weather)

    # Сохраняем профиль
    await set_profile(message.from_user.id, user_data['weight'], user_data['height'], user_data['age'],
                      user_data['activity'], city, goal_calories)

    await message.reply(
        f"Ваш профиль настроен! Норма воды: {water_intake} мл, Норма калорий: {goal_calories} ккал. "
        f"Используйте команду /check_progress для отслеживания прогресса.")

    await state.clear()  # Завершаем процесс и очищаем состояние


@dp.message(Command("check_progress"))
async def check_progress(message: Message):
    progress = await get_progress(message.from_user.id)
    await message.reply(progress)


@dp.message(Command("log_water"))
async def log_water_cmd(message: Message):
    try:
        # Разделяем команду и извлекаем количество воды
        command_parts = message.text.split()

        if len(command_parts) != 2:
            await message.reply("Пожалуйста, укажите количество воды, например: /log_water 500")
            return

        # Преобразуем количество воды в число
        try:
            amount = float(command_parts[1])
        except ValueError:
            await message.reply("Пожалуйста, укажите корректное количество воды (число).")
            return

        # Добавляем воду в базу
        await log_water(message.from_user.id, amount)

        # Получаем информацию о пользователе из базы данных
        user_profile = await get_profile(message.from_user.id)

        if user_profile:
            water_goal = user_profile['water_goal']  # Используем сохранённую норму воды

            # Получаем текущее количество выпитой воды
            current_water = await get_water_log(message.from_user.id)
            remaining_water = water_goal - current_water

            # Ответ пользователю с информацией о прогрессе
            if remaining_water > 0:
                await message.reply(
                    f"Записано {amount} мл воды. Осталось выпить {remaining_water:.2f} мл для достижения цели.")
            else:
                await message.reply(f"Записано {amount} мл воды. Цель достигнута!")
        else:
            await message.reply(
                "Не удалось найти ваш профиль. Пожалуйста, настройте его с помощью команды /set_profile.")

    except Exception as e:
        # Логируем ошибку для диагностики
        print(f"Ошибка при обработке команды /log_water: {e}")
        await message.reply("Произошла ошибка. Пожалуйста, попробуйте снова позже.")



@dp.message(Command("log_food"))
async def log_food_cmd(message: Message, state: FSMContext):
    # Извлекаем название продукта
    food_name = ' '.join(message.text.split()[1:])

    # Получаем калорийность продукта по API (например, через OpenFoodFacts)
    calories_per_100g = await get_calories(food_name)

    if calories_per_100g is None:
        # Если калорийность не найдена, спрашиваем у пользователя калорийность продукта
        await message.reply(
            f"🍌 {food_name.capitalize()} не найден в базе данных. Укажите калорийность продукта на 100 г.")

        # Переходим в состояние ожидания калорийности
        await state.set_state(FoodState.waiting_for_calories.state)
        await state.update_data(food_name=food_name)

    else:
        # Если калорийность найдена, продолжаем как обычно
        await message.reply(f"🍌 {food_name.capitalize()} — {calories_per_100g} ккал на 100 г. Сколько грамм вы съели?")

        # Переходим в состояние ожидания граммов
        await state.set_state(FoodState.waiting_for_grams.state)
        await state.update_data(food_name=food_name, calories_per_100g=calories_per_100g)
# Обработчик для ввода калорийности
# Обработчик для ввода калорийности
@dp.message(StateFilter(FoodState.waiting_for_calories))
async def log_food_calories(message: Message, state: FSMContext):
    try:
        # Получаем калорийность от пользователя
        calories_per_100g = float(message.text)

        # Сохраняем введённую калорийность в состоянии
        await state.update_data(calories_per_100g=calories_per_100g)

        # Спрашиваем, сколько грамм продукта съел пользователь
        food_name = (await state.get_data())['food_name']
        await message.reply(f"Сколько грамм {food_name} вы съели?")

        # Переходим к состоянию для ввода граммов
        await state.set_state(FoodState.waiting_for_grams.state)

    except ValueError:
        await message.reply("Пожалуйста, укажите корректную калорийность (число).")

# Обработчик для ввода граммов
# Обработчик для ввода граммов
@dp.message(StateFilter(FoodState.waiting_for_grams))
async def log_food_amount(message: Message, state: FSMContext):
    try:
        # Получаем количество грамм
        grams = float(message.text)

        # Извлекаем данные из состояния
        data = await state.get_data()
        calories_per_100g = data['calories_per_100g']
        food_name = data['food_name']

        # Рассчитываем калории на основе граммов
        calories = (calories_per_100g * grams) / 100

        # Логируем потребление еды
        await log_food(message.from_user.id, food_name, calories)

        # Отправляем результат пользователю
        await message.reply(f"Записано: {calories:.2f} ккал для {food_name} ({grams} г).")

        # Завершаем состояние
        await state.clear()

    except ValueError:
        await message.reply("Пожалуйста, введите корректное количество грамм (число).")

@dp.message(Command("log_workout"))
async def log_workout_cmd(message: Message):
    workout_data = message.text.split()[1:]
    workout_type = workout_data[0]
    workout_time = int(workout_data[1])
    calories_burned = workout_time * 10
    await log_workout(message.from_user.id, workout_type, workout_time, calories_burned)
    await message.reply(f"Записано: {workout_type} {workout_time} минут — {calories_burned} ккал.")


async def main():
    await create_tables()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(create_tables())
    asyncio.run(main())
