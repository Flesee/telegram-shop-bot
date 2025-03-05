FROM python:3.12-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование проекта
COPY . .

# Порт для Django
EXPOSE 8000

# Скрипт для инициализации проекта
RUN chmod +x /app/entrypoint.sh

# Запуск сервера через entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]