from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_successful_payment_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура после успешной оплаты
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🏠 Вернуться в меню", callback_data="start")
    builder.button(text="📋 Мои заказы", callback_data="my_orders")
    
    builder.adjust(1)
    
    return builder.as_markup()


def get_order_payment_keyboard(payment_url: str, payment_id: str) -> InlineKeyboardMarkup:
    """
    Клавиатура для перехода на страницу оплаты заказа
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(text="💳 Перейти к оплате", url=payment_url)
    builder.button(text="❌ Отменить платеж", callback_data=f"cancel_payment_{payment_id}")
    
    builder.adjust(1)
    
    return builder.as_markup()


def get_back_to_cart_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для возврата в корзину
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🛒 Вернуться в корзину", callback_data="cart")
    builder.adjust(1)
    
    return builder.as_markup()
