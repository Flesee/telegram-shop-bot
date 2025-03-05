from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.formatters import format_price
from typing import List, Optional, Any


def get_categories_keyboard(
    categories: List[Any], 
    is_main: bool = True, 
    current_page: int = 1, 
    total_pages: int = 1, 
    parent_id: Optional[int] = None
) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру со списком категорий и пагинацией.
    
    Args:
        categories: Список категорий для отображения
        is_main: Флаг, указывающий, являются ли категории основными
        current_page: Текущая страница пагинации
        total_pages: Общее количество страниц
        parent_id: ID родительской категории (для подкатегорий)
        
    Returns:
        Клавиатура с кнопками категорий и пагинацией
    """
    builder = InlineKeyboardBuilder()
    navigation_buttons = []
    
    for category in categories:
        if is_main:
            # Для основных категорий показываем подкатегории
            builder.button(
                text=category.name,
                callback_data=f"main_category_{category.id}"
            )
        else:
            # Для подкатегорий показываем товары
            builder.button(
                text=category.name,
                callback_data=f"category_{category.id}"
            )
    
    builder.adjust(1)
    
    # Добавляем кнопки пагинации, если страниц больше одной
    if total_pages > 1:
        # Кнопка "Назад" (если не на первой странице)
        if current_page > 1:
            if is_main:
                navigation_buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"main_categories_{current_page - 1}"))
            else:
                navigation_buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"subcategories_{parent_id}_{current_page - 1}"))
        else:
            # Пустая кнопка, если на первой странице
            navigation_buttons.append(InlineKeyboardButton(text=" ", callback_data="empty"))
        
        # Номер текущей страницы
        navigation_buttons.append(InlineKeyboardButton(text=f"{current_page}/{total_pages}", callback_data="empty"))
        
        # Кнопка "Вперед" (если не на последней странице)
        if current_page < total_pages:
            if is_main:
                navigation_buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"main_categories_{current_page + 1}"))
            else:
                navigation_buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"subcategories_{parent_id}_{current_page + 1}"))
        else:
            # Пустая кнопка, если на последней странице
            navigation_buttons.append(InlineKeyboardButton(text=" ", callback_data="empty"))
        
        builder.row(*navigation_buttons)

    if not is_main:
        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад к категориям",
                callback_data="back_to_main_categories"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="start"
            )
        )
    
    return builder.as_markup()


def get_products_keyboard(
    products: List[Any], 
    category_id: int, 
    current_page: int, 
    total_pages: int
) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с товарами и пагинацией.
    """
    builder = InlineKeyboardBuilder()
    navigation_buttons = []

    for product in products:
        builder.button(
            text=f"{product.name}",
            callback_data=f"product_{product.id}"
        )
    
    builder.adjust(1)

    if total_pages > 1:
        # Добавляем кнопки пагинации
        # Кнопка "Назад" (если не на первой странице)
        if current_page > 1:
            navigation_buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"category_{category_id}_{current_page - 1}"))
        else:
            # Пустая кнопка, если на первой странице
            navigation_buttons.append(InlineKeyboardButton(text=" ", callback_data="empty"))

        # Номер текущей страницы
        navigation_buttons.append(InlineKeyboardButton(text=f"{current_page}/{total_pages}", callback_data="empty"))

        # Кнопка "Вперед" (если не на последней странице)
        if current_page < total_pages:
            navigation_buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"category_{category_id}_{current_page + 1}"))
        else:
            # Пустая кнопка, если на последней странице
            navigation_buttons.append(InlineKeyboardButton(text=" ", callback_data="empty"))

        builder.row(*navigation_buttons)
    
    # Кнопка возврата к родительской категории
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=f"back_to_parent_category_{category_id}"
        )
    )
    
    return builder.as_markup()


def get_product_keyboard(product: Any, quantity: int = 1) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для отдельного товара с выбором количества.
    """
    builder = InlineKeyboardBuilder()

    builder.button(
        text="➖",
        callback_data=f"change_quantity_{product.id}_{max(1, quantity - 1)}"
    )
    
    builder.button(
        text=f"{quantity} шт.",
        callback_data="empty"
    )
    
    builder.button(
        text="➕",
        callback_data=f"change_quantity_{product.id}_{quantity + 1}"
    )

    builder.button(
        text="🛒 Добавить в корзину",
        callback_data=f"confirm_add_to_cart_{product.id}_{quantity}"
    )

    builder.button(
        text="🔙 Назад к товарам",
        callback_data=f"category_{product.category_id}"
    )

    builder.adjust(3, 1, 1)
    
    return builder.as_markup()


def get_product_added_keyboard(product: Any) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру после добавления товара в корзину.
    """
    builder = InlineKeyboardBuilder()

    builder.button(
        text="🛍️ Перейти в корзину",
        callback_data="cart"
    )

    builder.button(
        text="🔙 Назад к товарам",
        callback_data=f"category_{product.category_id}"
    )

    builder.adjust(1)
    
    return builder.as_markup()
