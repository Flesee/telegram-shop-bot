from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from datetime import datetime

from models import Order, OrderItem, Product
from services.cart_service import get_cart_items, clear_cart
from services.user_service import get_user


async def create_order_from_cart(session: AsyncSession, user_id: int, clear_cart_flag: bool = True):
    """Создание заказа из корзины пользователя
    
    Args:
        session: Сессия базы данных
        user_id: ID пользователя
        clear_cart_flag: Флаг очистки корзины после создания заказа
    
    Returns:
        Order: Созданный заказ или None, если корзина пуста
    """
    # Получаем товары из корзины
    cart_items = await get_cart_items(session, user_id)
    
    if not cart_items:
        return None
    
    # Получаем информацию о пользователе
    user = await get_user(session, user_id)
    
    # Создаем новый заказ
    order = Order(
        user_id=user_id,
        full_name=user.full_name if user else None,
        phone=user.phone if user else None,
        address=user.address if user else None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    session.add(order)
    await session.flush()  # Получаем ID заказа
    
    # Добавляем товары из корзины в заказ
    for cart_item, product in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=cart_item.quantity,
            price=product.price
        )
        session.add(order_item)
    
    # Очищаем корзину только если указан флаг
    if clear_cart_flag:
        await clear_cart(session, user_id)
    
    await session.commit()
    await session.refresh(order)
    return order


async def get_user_orders(session: AsyncSession, user_id: int):
    """Получение всех заказов пользователя"""
    result = await session.execute(
        select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc())
    )
    return result.scalars().all()


async def get_order_by_id(session: AsyncSession, order_id: int):
    """Получение заказа по ID"""
    result = await session.execute(select(Order).where(Order.id == order_id))
    return result.scalars().first()


async def get_order_items(session: AsyncSession, order_id: int):
    """Получение всех товаров в заказе"""
    result = await session.execute(
        select(OrderItem, Product)
        .join(Product, OrderItem.product_id == Product.id)
        .where(OrderItem.order_id == order_id)
    )
    return result.all()


async def update_order_status(session: AsyncSession, order_id: int, status: str):
    """Обновление статуса заказа"""
    await session.execute(
        update(Order)
        .where(Order.id == order_id)
        .values(status=status)
    )
    await session.commit()
