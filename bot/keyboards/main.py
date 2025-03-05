from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_main_keyboard() -> InlineKeyboardMarkup:
    """
    Создает основную клавиатуру бота.
    """
    builder = InlineKeyboardBuilder()

    builder.button(text="🛍 Каталог товаров", callback_data="catalog")
    builder.button(text="🛒 Корзина", callback_data="cart")
    builder.button(text="📦 Мои заказы", callback_data="my_orders")
    builder.button(text="❓ FAQ", callback_data="help")

    builder.adjust(1, 2, 1)

    return builder.as_markup()
