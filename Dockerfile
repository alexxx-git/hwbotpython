# Используем официальный образ Python 3.13
FROM python:3.13.1-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файлы проекта в контейнер
COPY . /app

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Указываем переменные окружения для корректной работы SQLite
ENV DATABASE_PATH="/app/bot_database.db"

# Открываем порт (если нужно, например, для webhook)
EXPOSE 8000

# Запускаем бота
CMD ["python3", "app/bot.py"]
