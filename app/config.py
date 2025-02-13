import os
from dotenv import load_dotenv
load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')  # Токен Telegram бота
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')  # Ключ API для OpenWeather
DB_NAME = os.getenv('DB_NAME')
NUTRITION_API_KEY = os.getenv('NUTRITION_API_KEY')
