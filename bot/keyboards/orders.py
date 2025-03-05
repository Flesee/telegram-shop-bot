from typing import List, Optional, Any

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from models.order import Order
from constants import get_order_status_text


def get_orders_list_keyboard(orders: Optional[List[Order]] = None, has_orders: bool = True) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для списка заказов пользователя.
    """
    builder = InlineKeyboardBuilder()
    
    # Если есть заказы, добавляем кнопки для каждого заказа
    if has_orders and orders:
        for order in orders:
            status_text = get_order_status_text(order.status)
            builder.button(
                text=f"Заказ #{order.id} - {status_text}",
                callback_data=f"order_details_{order.id}"
            )

    builder.button(
        text="🏠 Главное меню",
        callback_data="start"
    )

    builder.adjust(1)
    
    return builder.as_markup()


def get_order_details_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для просмотра деталей заказа.
    """
    builder = InlineKeyboardBuilder()

    builder.button(
        text="◀️ Назад к заказам",
        callback_data="my_orders"
    )

    builder.button(
        text="🏠 Главное меню",
        callback_data="start"
    )

    builder.adjust(1)
    
    return builder.as_markup()


def get_orders_keyboard(orders: Optional[List[Order]] = None, has_orders: bool = True) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для списка заказов пользователя.
    """
    builder = InlineKeyboardBuilder()

    if has_orders and orders:
        for order in orders:
            status_text = get_order_status_text(order.status)
            builder.button(
                text=f"Заказ #{order.id} - {status_text}",
                callback_data=f"order_details_{order.id}"
            )
    
    builder.button(
        text="📦 Каталог",
        callback_data="catalog"
    )
    
    builder.button(
        text="🔙 Главное меню",
        callback_data="start"
    )

    builder.adjust(1)

    return builder.as_markup()
    
