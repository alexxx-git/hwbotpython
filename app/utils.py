from config import OPENWEATHER_API_KEY
import aiohttp

def calculate_water_intake(weight, activity_minutes, hot_weather=False):
    water_intake = weight * 30  # Базовая норма
    water_intake += 500 * (activity_minutes / 30)  # За каждую 30-минутную активность
    if hot_weather:
        water_intake += 1000  # Дополнительные 1000 мл для жаркой погоды
    return round(water_intake,0)

def calculate_calories(weight, height, age, activity_level):
    # Основная формула для расчёта калорий
    base_calories = 10 * weight + 6.25 * height - 5 * age
    # Добавим калории за активность
    additional_calories = activity_level * 10  # 200-400 в зависимости от активности
    return base_calories + additional_calories


async def get_temperature(city: str) -> float:
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            return data["main"]["temp"]  # Возвращаем температуру в градусах Цельсия


async def get_calories(product_name):
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={product_name}&search_simple=1&json=1"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()

                # Проверка на наличие продуктов в ответе
                if 'products' in data and data['products']:
                    product = data['products'][0]  # Берём первый продукт из списка
                    calories = product.get('nutriments', {}).get('energy-kcal', 'Неизвестно')
                    return calories
                return None
            else:
                return "Ошибка запроса. Пожалуйста, попробуйте позже."
