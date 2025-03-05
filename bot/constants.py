ORDER_STATUS_TRANSLATIONS = {
    "new": "Новый",
    "pending": "Ожидает оплаты",
    "paid": "Оплачен",
    "shipped": "Отправлен",
    "delivered": "Доставлен",
    "cancelled": "Отменен"
}

def get_order_status_text(status: str) -> str:
    """Получает текстовое представление статуса заказа на русском языке"""
    return ORDER_STATUS_TRANSLATIONS.get(status, status) 