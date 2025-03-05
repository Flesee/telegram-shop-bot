from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from database import get_session
from services.cart_service import get_cart_items, update_cart_item, remove_from_cart, clear_cart
from utils.logger import logger
from utils.formatters import format_price, format_total_price
from keyboards import (
    get_cart_keyboard, get_cart_item_keyboard,
    get_cart_empty_keyboard
)
from .start import callback_start
from models.user import User


# Определение состояний для FSM
class OrderDelivery(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_phone = State()
    waiting_for_address = State()
    confirm_info = State()


cart_router = Router()


@cart_router.callback_query(F.data == "cart")
async def show_cart(callback: CallbackQuery):
    """Показать содержимое корзины"""
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} открыл корзину")
    
    async for session in get_session():
        cart_items = await get_cart_items(session, user_id)
        
        if not cart_items:
            await callback.message.edit_text(
                "🛒 Ваша корзина пуста. Добавьте товары из каталога.",
                reply_markup=get_cart_empty_keyboard()
            )
            await callback.answer()
            return
        
        total_price = 0
        cart_text = "🛒 Ваша корзина:\n\n"
        
        for i, (cart_item, product) in enumerate(cart_items, 1):
            # Форматируем цену и общую стоимость позиции
            price_str = format_price(product.price)
            
            item_total = product.price * cart_item.quantity
            total_price += item_total
            
            # Форматируем общую стоимость позиции
            item_total_str = format_price(item_total)
            
            cart_text += (
                f"{i}. {product.name}\n"
                f"   Цена: {price_str} × {cart_item.quantity} шт. = {item_total_str}\n\n"
            )
        
        # Форматируем общую стоимость корзины
        total_price_str = format_price(total_price)
        
        cart_text += f"Общая стоимость: {total_price_str}"

        await callback.message.edit_text(
            cart_text,
            reply_markup=get_cart_keyboard(cart_items, total_price)
        )
    
    await callback.answer()


@cart_router.callback_query(F.data.startswith("cart_item_"))
async def show_cart_item(callback: CallbackQuery):
    """Показать отдельный товар в корзине"""
    cart_item_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    logger.info(f"Пользователь {user_id} открыл товар {cart_item_id} в корзине")
    
    async for session in get_session():
        cart_items = await get_cart_items(session, user_id)
        
        # Находим нужный товар
        cart_item_data = next(
            ((cart_item, product) for cart_item, product in cart_items if cart_item.id == cart_item_id),
            None
        )
        
        if not cart_item_data:
            await callback.answer("Товар не найден в корзине", show_alert=True)
            return
        
        cart_item, product = cart_item_data
        
        # Форматируем цену и общую стоимость
        price_str, total_str = format_total_price(product.price, cart_item.quantity)

        text = (
            f"🛍️ {product.name}\n\n"
            f"💰 Цена за единицу: {price_str}\n"
            f"🔢 Количество: {cart_item.quantity} шт.\n"
            f"💵 Общая стоимость: {total_str}"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_cart_item_keyboard(cart_item)
        )
    
    await callback.answer()


@cart_router.callback_query(F.data.startswith("cart_increase_"))
async def increase_quantity(callback: CallbackQuery):
    """Увеличить количество товара в корзине"""
    cart_item_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    logger.info(f"Пользователь {user_id} увеличивает количество товара {cart_item_id} в корзине")
    
    async for session in get_session():
        cart_items = await get_cart_items(session, user_id)
        
        # Находим нужный товар
        cart_item_data = next(
            ((cart_item, product) for cart_item, product in cart_items if cart_item.id == cart_item_id),
            None
        )
        
        if not cart_item_data:
            await callback.answer("Товар не найден в корзине", show_alert=True)
            return
        
        cart_item, product = cart_item_data
        
        new_quantity = cart_item.quantity + 1
        await update_cart_item(session, cart_item.id, new_quantity)
        
        # Форматируем цену и общую стоимость
        price_str, total_str = format_total_price(product.price, new_quantity)
        
        # Обновляем сообщение
        text = (
            f"🛍️ {product.name}\n\n"
            f"💰 Цена за единицу: {price_str}\n"
            f"🔢 Количество: {new_quantity} шт.\n"
            f"💵 Общая стоимость: {total_str}"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_cart_item_keyboard(cart_item, new_quantity)
        )
    
    await callback.answer()


@cart_router.callback_query(F.data.startswith("cart_decrease_"))
async def decrease_quantity(callback: CallbackQuery):
    """Уменьшить количество товара в корзине"""
    cart_item_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    logger.info(f"Пользователь {user_id} уменьшает количество товара {cart_item_id} в корзине")
    
    async for session in get_session():
        cart_items = await get_cart_items(session, user_id)
        
        # Находим нужный товар
        cart_item_data = next(
            ((cart_item, product) for cart_item, product in cart_items if cart_item.id == cart_item_id),
            None
        )
        
        if not cart_item_data:
            await callback.answer("Товар не найден в корзине", show_alert=True)
            return
        
        cart_item, product = cart_item_data
        
        # Если количество равно 1, удаляем товар из корзины
        if cart_item.quantity == 1:
            await remove_from_cart(session, cart_item.id)
            
            # Проверяем, остались ли товары в корзине
            cart_items = await get_cart_items(session, user_id)
            
            if cart_items:
                # Если в корзине остались товары, возвращаемся к корзине
                await show_cart(callback)
            else:
                await callback.answer("🛒 Корзина пуста!", show_alert=True)
                await callback_start(callback)
            return
        
        # Уменьшаем количество
        new_quantity = cart_item.quantity - 1
        await update_cart_item(session, cart_item.id, new_quantity)
        
        # Форматируем цену и общую стоимость
        price_str, total_str = format_total_price(product.price, new_quantity)
        
        # Обновляем сообщение
        text = (
            f"🛍️ {product.name}\n\n"
            f"💰 Цена за единицу: {price_str}\n"
            f"🔢 Количество: {new_quantity} шт.\n"
            f"💵 Общая стоимость: {total_str}"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_cart_item_keyboard(cart_item, new_quantity)
        )
    
    await callback.answer()


@cart_router.callback_query(F.data.startswith("cart_remove_"))
async def remove_item(callback: CallbackQuery):
    """Удалить товар из корзины"""
    cart_item_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    logger.info(f"Пользователь {user_id} удаляет товар {cart_item_id} из корзины")
    
    async for session in get_session():
        # Удаляем товар
        await remove_from_cart(session, cart_item_id)
        await callback.answer("Товар удален из корзины", show_alert=True)
        
        # Проверяем, остались ли товары в корзине
        cart_items = await get_cart_items(session, user_id)
        
        if cart_items:
            # Если в корзине остались товары, возвращаемся к корзине
            await show_cart(callback)
        else:
            # Если корзина пуста, возвращаемся в главное меню
            await callback.answer("🛒 Корзина пуста!", show_alert=True)
            await callback_start(callback)


@cart_router.callback_query(F.data == "cart_clear")
async def clear_user_cart(callback: CallbackQuery):
    """Очистить корзину"""
    user_id = callback.from_user.id
    
    logger.info(f"Пользователь {user_id} очищает корзину")
    
    async for session in get_session():
        # Получаем пользователя по Telegram ID
        user_result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = user_result.scalars().first()
        
        if user:
            await clear_cart(session, user.id)
            await callback.answer("✅ Корзина очищена", show_alert=True)
        else:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            
        await callback_start(callback)
