"""
Модуль с функциями для форматирования данных
"""

import re

def format_price(price: float) -> str:
    """
    Форматирует цену для лучшего отображения
    """
    if price == int(price):
        return f"{int(price):,}".replace(",", " ") + " руб."
    else:
        return f"{price:,.2f}".replace(",", " ").replace(".", ",") + " руб."


def format_total_price(price: float, quantity: int) -> tuple[str, str]:
    """
    Форматирует общую стоимость товара с учетом количества
    """
    price_str = format_price(price)
    
    # Рассчитываем общую стоимость
    total_price = price * quantity
    
    if total_price == int(total_price):
        total_price_str = f"{int(total_price):,}".replace(",", " ") + " руб."
    else:
        total_price_str = f"{total_price:,.2f}".replace(",", " ").replace(".", ",") + " руб."
    
    return price_str, total_price_str


def format_phone_number(phone):
    """
    Форматирование телефонного номера в стандартный формат +7XXXXXXXXXX
    """
    if not phone:
        return None
    
    # Извлекаем все цифры из строки
    digits = re.sub(r'\D', '', phone)

    if len(digits) == 11:
        if digits.startswith('8') or digits.startswith('7'):
            return f"+7{digits[1:]}"
    elif len(digits) == 10:
        return f"+7{digits}"
    
    if digits:
        return f"+{digits}"
    
    return None

def format_order_details(order, items=None):
    """
    Форматирует детали заказа для отображения пользователю
    
    Args:
        order: Объект заказа из базы данных
        items: Список товаров в заказе (опционально)
        
    Returns:
        Отформатированная строка с деталями заказа
    """
    result = [
        f"🧾 <b>Заказ #{order.id}</b>",
        f"📅 Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}",
        f"💰 Сумма: {format_price(order.total_amount)}",
        f"📦 Статус: {order.status}"
    ]
    
    if order.payment_status:
        result.append(f"💳 Статус оплаты: {order.payment_status}")
    
    if order.address:
        result.append(f"🏠 Адрес доставки: {order.address}")
    
    if items:
        result.append("\n📋 <b>Товары в заказе:</b>")
        for i, item in enumerate(items, 1):
            price_str, total_str = format_total_price(item.price, item.quantity)
            result.append(f"{i}. {item.product_name} - {item.quantity} шт. x {price_str} = {total_str}")
    
    return "\n".join(result) 