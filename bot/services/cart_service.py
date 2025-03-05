from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from sqlalchemy.sql import text
from datetime import datetime

from models import CartItem, Product, User
from services.user_service import get_or_create_user


async def get_cart_items(session: AsyncSession, user_id: int):
    """Получение всех товаров в корзине пользователя"""
    user_result = await session.execute(
        select(User).where(User.user_id == user_id)
    )
    user = user_result.scalars().first()
    
    if not user:
        return []

    result = await session.execute(
        select(CartItem, Product)
        .join(Product, CartItem.product_id == Product.id)
        .where(CartItem.user_id == user.id)
    )
    return result.all()


async def get_cart_item(session: AsyncSession, user_id: int, product_id: int):
    """Получение элемента корзины по ID пользователя и ID товара"""
    # Получаем или создаем пользователя
    user = await get_or_create_user(session, user_id)
    if not user:
        return None

    result = await session.execute(
        select(CartItem)
        .where(CartItem.user_id == user.id, CartItem.product_id == product_id)
    )
    return result.scalars().first()


async def add_to_cart(session: AsyncSession, user_id: int, product_id: int, quantity: int = 1):
    """Добавление товара в корзину"""
    # Получаем или создаем пользователя
    user = await get_or_create_user(session, user_id)
    if not user:
        return None

    # Проверяем, есть ли уже такой товар в корзине
    cart_item = await get_cart_item(session, user_id, product_id)
    
    if cart_item:
        # Если товар уже есть, добавляем к текущему количеству
        cart_item.quantity += quantity
        cart_item.updated_at = datetime.now()
    else:
        # Создаем новый элемент корзины
        cart_item = CartItem(
            user_id=user.id,
            product_id=product_id,
            quantity=quantity,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        session.add(cart_item)
    
    await session.commit()
    return cart_item


async def update_cart_item(session: AsyncSession, cart_item_id: int, quantity: int):
    """Обновление количества товара в корзине по ID элемента корзины"""
    result = await session.execute(
        select(CartItem).where(CartItem.id == cart_item_id)
    )
    cart_item = result.scalars().first()

    if cart_item:
        if quantity <= 0:
            # Если количество <= 0, удаляем товар из корзины
            await session.execute(
                delete(CartItem).where(CartItem.id == cart_item_id)
            )
        else:
            # Иначе обновляем количество
            cart_item.quantity = quantity
            cart_item.updated_at = datetime.now()

        await session.commit()
        return True

    return False


async def remove_from_cart(session: AsyncSession, cart_item_id: int):
    """Удаление товара из корзины по ID элемента корзины"""
    await session.execute(
        delete(CartItem)
        .where(CartItem.id == cart_item_id)
    )
    await session.commit()
    return True


async def clear_cart(session: AsyncSession, user_id: int):
    """Очистка корзины пользователя"""
    await session.execute(
        delete(CartItem)
        .where(CartItem.user_id == user_id)
    )
    await session.commit()
    return True
