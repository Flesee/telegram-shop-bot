#!/bin/bash

# Создаем директорию для логов
mkdir -p /app/logs

# Проверяем, существует ли файл settings.py
if [ ! -f /app/shopbot_admin/settings.py ]; then
    echo "Инициализация Django проекта..."
    django-admin startproject shopbot_admin .
    
    # Заменяем настройки базы данных в settings.py
    sed -i 's/django.db.backends.sqlite3/django.db.backends.postgresql/g' shopbot_admin/settings.py
    sed -i "s/'NAME': BASE_DIR \/ 'db.sqlite3',/'NAME': os.environ.get('DB_NAME', 'shopbot_db'),\n        'USER': os.environ.get('DB_USER', 'postgres'),\n        'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),\n        'HOST': os.environ.get('DB_HOST', 'db'),\n        'PORT': os.environ.get('DB_PORT', '5432'),/g" shopbot_admin/settings.py
    
    # Добавляем импорт os в начало файла settings.py
    sed -i '1s/^/import os\n/' shopbot_admin/settings.py
    
    # Создаем приложение для управления магазином
    python manage.py startapp shop
    
    # Добавляем приложение в INSTALLED_APPS
    sed -i "/INSTALLED_APPS = \[/a \    'shop'," shopbot_admin/settings.py
    
    echo "Django проект успешно инициализирован!"
fi

# Функция для проверки доступности базы данных
wait_for_db() {
    echo "Ожидание готовности базы данных..."
    while ! python << END
import sys
import os
import psycopg2
try:
    psycopg2.connect(
        dbname=os.environ.get('DB_NAME', 'shopbot_db'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'postgres'),
        host=os.environ.get('DB_HOST', 'db'),
        port=os.environ.get('DB_PORT', '5432')
    )
except psycopg2.OperationalError:
    sys.exit(1)
sys.exit(0)
END
    do
        echo "База данных недоступна, ожидание..."
        sleep 1
    done
    echo "База данных готова!"
}

# Исправляем настройки логирования
if grep -q "'/logs/django.log'" shopbot_admin/settings.py; then
    echo "Исправляем пути к файлам логов..."
    sed -i "s|'/logs/django.log'|'/app/logs/django.log'|g" shopbot_admin/settings.py
fi

# Ждем готовности базы данных перед применением миграций
wait_for_db

# Применяем миграции
python manage.py migrate

# Создаем суперпользователя, если его нет
if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ] && [ "$DJANGO_SUPERUSER_EMAIL" ]; then
    python manage.py createsuperuser --noinput
fi

# Собираем статические файлы
python manage.py collectstatic --noinput

# Запускаем сервер
exec gunicorn shopbot_admin.wsgi:application --bind 0.0.0.0:8000
