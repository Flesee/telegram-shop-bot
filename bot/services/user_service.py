from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from datetime import datetime

from models import User


async def get_user(session: AsyncSession, user_id: int):
    """Получение пользователя по ID"""
    result = await session.execute(select(User).where(User.user_id == user_id))
    return result.scalars().first()


async def get_all_users(session: AsyncSession) -> list[User]:
    """Получение всех пользователей"""
    result = await session.execute(select(User))
    return list(result.scalars().all())


async def create_user(session: AsyncSession, user_id: int, username: str = None):
    """Создание нового пользователя"""
    now = datetime.now()
    user = User(
        user_id=user_id, 
        username=username,
        created_at=now,
        updated_at=now
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_or_create_user(session: AsyncSession, user_id: int, username: str = None):
    """Получение существующего пользователя или создание нового"""
    user = await get_user(session, user_id)
    if not user:
        user = await create_user(session, user_id, username)
    return user


async def update_user_delivery_info(session: AsyncSession, user_id: int, full_name: str = None, 
                                   phone: str = None, address: str = None):
    """Обновление информации о доставке пользователя"""
    update_data = {}
    if full_name is not None:
        update_data["full_name"] = full_name
    if phone is not None:
        update_data["phone"] = phone
    if address is not None:
        update_data["address"] = address
    
    if update_data:
        update_data["updated_at"] = datetime.now()
        await session.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(**update_data)
        )
        await session.commit()
    
    return await get_user(session, user_id)


async def get_user_delivery_info(session: AsyncSession, user_id: int):
    """Получение информации о доставке пользователя"""
    user = await get_user(session, user_id)
    if not user:
        return None
    
    return {
        "full_name": user.full_name,
        "phone": user.phone,
        "address": user.address,
        "username": user.username
    }


async def has_delivery_info(session: AsyncSession, user_id: int):
    """Проверка наличия информации о доставке у пользователя"""
    user = await get_user(session, user_id)
    if not user:
        return False
    
    return user.full_name is not None and user.phone is not None and user.address is not None
