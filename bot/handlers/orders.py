from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database import get_session
from services.order_service import get_user_orders, get_order_by_id, get_order_items
from utils.logger import logger
from utils.formatters import format_price
from keyboards.orders import get_orders_keyboard, get_order_details_keyboard
from constants import get_order_status_text

orders_router = Router()


@orders_router.callback_query(F.data == "my_orders")
async def show_orders(callback: CallbackQuery):
    """Показать список заказов пользователя"""
    user_id = callback.from_user.id
    
    logger.info(f"Пользователь {user_id} просматривает свои заказы")
    
    async for session in get_session():
        # Получаем заказы пользователя
        orders = await get_user_orders(session, user_id)
        
        if not orders:
            await callback.message.edit_text(
                "📦 У вас пока нет заказов.\n\n"
                "Вы можете сделать заказ в нашем каталоге товаров.",
                reply_markup=get_orders_keyboard(has_orders=False)
            )
            await callback.answer()
            return

        orders_text = "📋 Ваши заказы:\n\n"
        await callback.message.edit_text(
            orders_text,
            reply_markup=get_orders_keyboard(orders=orders)
        )
    
    await callback.answer()


@orders_router.callback_query(F.data.startswith("order_details_"))
async def show_order_details(callback: CallbackQuery):
    """Показать детали заказа"""
    order_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    logger.info(f"Пользователь {user_id} просматривает детали заказа {order_id}")
    
    async for session in get_session():
        # Получаем заказ по ID
        order = await get_order_by_id(session, order_id)
        
        if not order or order.user_id != user_id:
            await callback.answer("Заказ не найден", show_alert=True)
            return

        order_items = await get_order_items(session, order_id)
        
        if not order_items:
            await callback.answer("В заказе нет товаров", show_alert=True)
            return
        
        # Определяем статус заказа на русском языке
        status_text = get_order_status_text(order.status)
        
        # Форматируем дату создания заказа
        created_at = order.created_at.strftime("%d.%m.%Y %H:%M")

        details_text = f"📦 Заказ #{order.id}\n\n"

        if order.full_name and order.phone and order.address:
            details_text += (
                f"📬 Информация о доставке:\n\n"
                f"👤 ФИО: {order.full_name}\n"
                f"📱 Телефон: {order.phone}\n"
                f"🏠 Адрес: {order.address}\n\n"
            )

        details_text += "📋 Товары в заказе:\n\n"

        total_price = 0
        for i, item_data in enumerate(order_items, 1):
            order_item, product = item_data
            
            # Получаем цену из OrderItem
            price = order_item.price
            price_str = format_price(price)
            
            # Рассчитываем общую стоимость позиции
            item_total = price * order_item.quantity
            total_price += item_total
            
            # Форматируем общую стоимость позиции
            item_total_str = format_price(item_total)
            
            details_text += (
                f"{i}. {product.name}\n"
                f"   Цена: {price_str} × {order_item.quantity} шт. = {item_total_str}\n\n"
            )
        
        # Форматируем общую стоимость заказа
        total_price_str = format_price(total_price)

        details_text += (
            f"💰 Общая стоимость: {total_price_str}\n"
            f"📅 Дата заказа: {created_at}\n"
            f"🔄 Статус: {status_text}\n"
        )
        
        await callback.message.edit_text(
            details_text,
            reply_markup=get_order_details_keyboard()
        )
    
    await callback.answer()
