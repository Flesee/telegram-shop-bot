from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.formatters import format_price


def get_cart_keyboard(cart_items, total_price):
    """Клавиатура для корзины"""
    keyboard = InlineKeyboardBuilder()

    # Добавляем кнопки для каждого товара в корзине
    for cart_item, product in cart_items:
        keyboard.button(
            text=f"{product.name} ({cart_item.quantity} шт.)",
            callback_data=f"cart_item_{cart_item.id}"
        )

    # Добавляем кнопки для оформления заказа и очистки корзины
    keyboard.button(
        text="🧹 Очистить корзину",
        callback_data="cart_clear"
    )

    keyboard.button(
        text=f"💳 Оформить заказ ({format_price(total_price)})",
        callback_data="checkout"
    )

    # Кнопка возврата в главное меню
    keyboard.button(
        text="🔙 Назад",
        callback_data="start"
    )

    # Устанавливаем ширину в 1 кнопку
    keyboard.adjust(1)

    return keyboard.as_markup()


def get_cart_item_keyboard(cart_item, quantity=None):
    """Клавиатура для отдельного товара в корзине"""
    builder = InlineKeyboardBuilder()
    
    # Используем переданное количество или берем из объекта
    qty = quantity if quantity is not None else cart_item.quantity
    
    # Кнопки изменения количества
    builder.row(
        InlineKeyboardButton(text="➖", callback_data=f"cart_decrease_{cart_item.id}"),
        InlineKeyboardButton(text=f"{qty} шт.", callback_data="cart_quantity"),
        InlineKeyboardButton(text="➕", callback_data=f"cart_increase_{cart_item.id}")
    )

    builder.button(
        text="🗑️ Удалить",
        callback_data=f"cart_remove_{cart_item.id}"
    )

    builder.button(
        text="🔙 Назад к корзине",
        callback_data="cart"
    )

    builder.adjust(3, 1, 1)
    
    return builder.as_markup()


def get_cart_empty_keyboard():
    """Клавиатура для пустой корзины"""
    builder = InlineKeyboardBuilder()

    builder.button(
        text="📋 Перейти в каталог",
        callback_data="catalog"
    )

    builder.button(
        text="🔙 Главное меню",
        callback_data="start"
    )

    builder.adjust(1)
    
    return builder.as_markup()


def get_checkout_keyboard(edit_mode=False, has_delivery_info=False):
    """Клавиатура для оформления заказа"""
    builder = InlineKeyboardBuilder()
    
    if has_delivery_info:
        # Если данные о доставке уже есть
        if edit_mode:
            builder.button(
                text="✅ Подтвердить данные",
                callback_data="checkout_confirm"
            )
        else:
            # Режим просмотра данных
            builder.button(
                text="✏️ Изменить данные",
                callback_data="checkout_edit"
            )
            
            builder.button(
                text="💳 Перейти к оплате",
                callback_data="checkout_payment"
            )
    else:
        builder.button(
            text="❌ Отменить",
            callback_data="checkout_cancel"
        )

    builder.button(
        text="🔙 Вернуться в корзину",
        callback_data="cart"
    )

    builder.adjust(1)
    
    return builder.as_markup()
