import os
import sys
from alembic.config import Config
from alembic import command

# Добавляем корневую директорию проекта в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATABASE_URL


def run_migrations():
    """Запуск миграций базы данных"""
    # Создаем конфигурацию Alembic
    alembic_cfg = Config("migrations/alembic.ini")
    
    # Устанавливаем URL базы данных из конфигурации
    alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
    
    # Запускаем миграции
    command.upgrade(alembic_cfg, "head")
    
    print("✅ Миграции успешно применены")


if __name__ == "__main__":
    run_migrations() 