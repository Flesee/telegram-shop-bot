from aiogram import Router
from .start import start_router
from .catalog import catalog_router
from .cart import cart_router
from .delivery import delivery_router
from .payment import payment_router
from .orders import orders_router
from .faq import faq_router

# Создаем главный роутер для объединения всех роутеров
main_router = Router()

# Подключаем все роутеры к главному
main_router.include_router(start_router)
main_router.include_router(catalog_router)
main_router.include_router(cart_router)
main_router.include_router(delivery_router)
main_router.include_router(orders_router)
main_router.include_router(payment_router)
main_router.include_router(faq_router)

__all__ = ["main_router"]
