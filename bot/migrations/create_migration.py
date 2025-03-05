import os
import sys
import asyncio
from alembic.config import Config
from alembic import command

# Добавляем корневую директорию проекта в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATABASE_URL


async def create_migration(message="New migration"):
    """Создание новой миграции"""
    # Создаем конфигурацию Alembic
    alembic_cfg = Config("migrations/alembic.ini")
    
    # Устанавливаем URL базы данных из конфигурации
    alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
    
    # Создаем новую миграцию
    command.revision(alembic_cfg, autogenerate=True, message=message)
    
    print(f"✅ Миграция '{message}' успешно создана")


if __name__ == "__main__":
    # Получаем сообщение для миграции из аргументов командной строки
    message = sys.argv[1] if len(sys.argv) > 1 else "New migration"
    
    asyncio.run(create_migration(message)) 