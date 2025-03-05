from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import get_session
from services.cart_service import get_cart_items
from services.user_service import has_delivery_info, update_user_delivery_info, get_user_delivery_info
from utils.logger import logger
from utils.formatters import format_price, format_phone_number
from keyboards import get_checkout_keyboard, get_cart_keyboard


# Определение состояний для FSM
class DeliveryInfo(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_phone = State()
    waiting_for_address = State()


delivery_router = Router()


def calculate_total_price(cart_items):
    total_price = 0
    for cart_item, product in cart_items:
        item_total = product.price * cart_item.quantity
        total_price += item_total
    return total_price


@delivery_router.callback_query(F.data == "checkout")
async def process_checkout(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия на кнопку 'Оформить заказ'"""
    user_id = callback.from_user.id
    
    logger.info(f"Пользователь {user_id} начинает оформление заказа")
    
    async for session in get_session():
        # Проверяем, есть ли товары в корзине
        cart_items = await get_cart_items(session, user_id)
        if not cart_items:
            await callback.answer("Корзина пуста, невозможно оформить заказ", show_alert=True)
            return
        
        # Проверяем, есть ли у пользователя сохраненные данные доставки
        has_info = await has_delivery_info(session, user_id)
        
        if has_info:
            # Если данные уже есть, показываем их и предлагаем подтвердить или изменить
            delivery_info = await get_user_delivery_info(session, user_id)

            total_price = calculate_total_price(cart_items)
            total_price_str = format_price(total_price)
            
            await callback.message.edit_text(
                f"📦 Данные доставки:\n\n"
                f"👤 ФИО: {delivery_info['full_name']}\n"
                f"📱 Телефон: {delivery_info['phone']}\n"
                f"🏠 Адрес: {delivery_info['address']}\n\n"
                f"💰 Общая стоимость: {total_price_str}",
                reply_markup=get_checkout_keyboard(edit_mode=False, has_delivery_info=True)
            )
        else:
            # Если данных нет, запрашиваем ФИО
            await state.set_state(DeliveryInfo.waiting_for_full_name)
            
            # Создаем клавиатуру с кнопкой отмены
            await callback.message.edit_text(
                "Пожалуйста, введите ваше ФИО:",
                reply_markup=get_checkout_keyboard(edit_mode=False, has_delivery_info=False)
            )
    
    await callback.answer()


@delivery_router.callback_query(F.data == "checkout_edit")
async def edit_delivery_info(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия на кнопку 'Изменить данные'"""
    user_id = callback.from_user.id
    
    logger.info(f"Пользователь {user_id} редактирует данные доставки")
    
    # Переходим к вводу ФИО
    await state.set_state(DeliveryInfo.waiting_for_full_name)
    
    await callback.message.edit_text(
        "Пожалуйста, введите ваше ФИО:",
        reply_markup=get_checkout_keyboard(edit_mode=False, has_delivery_info=False)
    )
    
    await callback.answer()


@delivery_router.message(DeliveryInfo.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    """Обработка ввода ФИО"""
    user_id = message.from_user.id
    full_name = message.text.strip()

    logger.info(f"Пользователь {user_id} ввел ФИО: {full_name}")
    
    if not full_name:
        await message.answer("ФИО не может быть пустым. Пожалуйста, введите ваше ФИО:")
        return
    
    # Сохраняем ФИО в состоянии
    await state.update_data(full_name=full_name)
    
    # Переходим к вводу телефона
    await state.set_state(DeliveryInfo.waiting_for_phone)
    
    await message.answer(
        "Пожалуйста, введите ваш номер телефона:",
        reply_markup=get_checkout_keyboard(edit_mode=False, has_delivery_info=False)
    )


@delivery_router.message(DeliveryInfo.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обработка ввода телефона"""
    user_id = message.from_user.id
    phone_input = message.text.strip()

    logger.info(f"Пользователь {user_id} ввел номер телефона: {phone_input}")
    
    # Форматируем телефон
    phone = format_phone_number(phone_input)
    
    if not phone:
        await message.answer("Некорректный номер телефона. Пожалуйста, введите номер в формате +7XXXXXXXXXX:")
        return
    
    # Сохраняем телефон в состоянии
    await state.update_data(phone=phone)
    
    # Переходим к вводу адреса
    await state.set_state(DeliveryInfo.waiting_for_address)
    
    await message.answer(
        "Пожалуйста, введите адрес доставки:",
        reply_markup=get_checkout_keyboard(edit_mode=False, has_delivery_info=False)
    )


@delivery_router.message(DeliveryInfo.waiting_for_address)
async def process_address(message: Message, state: FSMContext):
    """Обработка ввода адреса"""
    user_id = message.from_user.id
    address = message.text.strip()

    logger.info(f"Пользователь {user_id} ввел адрес: {address}")
    
    if not address:
        await message.answer("Адрес не может быть пустым. Пожалуйста, введите адрес доставки:")
        return
    
    # Сохраняем адрес в состоянии
    await state.update_data(address=address)
    
    # Получаем все данные из состояния
    data = await state.get_data()
    full_name = data.get("full_name")
    phone = data.get("phone")
    
    async for session in get_session():
        # Сохраняем данные пользователя в базе
        await update_user_delivery_info(
            session, user_id,
            full_name=full_name,
            phone=phone,
            address=address
        )
        
        # Получаем товары из корзины для отображения общей стоимости
        cart_items = await get_cart_items(session, user_id)

        total_price = calculate_total_price(cart_items)
        total_price_str = format_price(total_price)
        
        # Показываем подтверждение данных
        await message.answer(
            f"📦 Данные доставки:\n\n"
            f"👤 ФИО: {full_name}\n"
            f"📱 Телефон: {phone}\n"
            f"🏠 Адрес: {address}\n\n"
            f"💰 Общая стоимость: {total_price_str}",
            reply_markup=get_checkout_keyboard(edit_mode=False, has_delivery_info=True)
        )


@delivery_router.callback_query(F.data == "checkout_cancel")
async def cancel_checkout(callback: CallbackQuery, state: FSMContext):
    """Отмена оформления заказа"""
    user_id = callback.from_user.id
    
    logger.info(f"Пользователь {user_id} отменил оформление заказа")
    
    # Очищаем состояние
    await state.clear()
    
    async for session in get_session():
        # Возвращаемся в корзину
        cart_items = await get_cart_items(session, user_id)

        total_price = calculate_total_price(cart_items)
        total_price_str = format_price(total_price)
        
        await callback.message.edit_text(
            f"🛒 Корзина:\n\n"
            f"Товары в корзине: {len(cart_items)}\n"
            f"Общая стоимость: {total_price_str}",
            reply_markup=get_cart_keyboard(cart_items, total_price_str)
        )
    
    await callback.answer()
