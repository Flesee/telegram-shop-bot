import asyncio
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery

from database import get_session
from services.payment_service import init_payment, check_payment_status, update_order_payment_status, delete_unpaid_order
from services.cart_service import clear_cart, get_cart_items
from services.user_service import get_user_delivery_info
from utils.logger import logger
from keyboards.payment import get_order_payment_keyboard, get_successful_payment_keyboard, get_back_to_cart_keyboard
from handlers.cart import show_cart
from utils.formatters import format_price


payment_router = Router()

# Словарь для хранения задач проверки платежей
payment_tasks = {}


@payment_router.callback_query(F.data == "checkout_payment")
async def process_payment(callback: CallbackQuery):
    """
    Обработчик для инициализации платежа
    """
    user_id = callback.from_user.id

    logger.info(f"Пользователь {user_id} начал процесс оплаты")
    
    async for session in get_session():
        user_info = await get_user_delivery_info(session, user_id)

        if not user_info.get('address') or not user_info.get('phone'):
            await callback.answer("Для оформления заказа необходимо указать адрес и телефон", show_alert=True)
            return

        # Инициализируем платеж
        payment_data = await init_payment(session, user_id, user_info)
    
        if not payment_data or not payment_data.get('payment_url'):
            await callback.answer("Не удалось создать платеж. Попробуйте позже.", show_alert=True)
            return

        cart_items = await get_cart_items(session, user_id)
        total_amount = sum(item[0].quantity * item[1].price for item in cart_items)
        formatted_amount = format_price(total_amount)

        # Отправляем сообщение с информацией о платеже
        await callback.message.edit_text(
            f"💳 Оплата заказа\n\n"
            f"Сумма к оплате: {formatted_amount}\n\n"
            f"Для оплаты нажмите на кнопку ниже. После оплаты статус заказа обновится автоматически.",
            reply_markup=get_order_payment_keyboard(payment_data.get('payment_url'), payment_data.get('payment_id'))
        )

        # Запускаем задачу проверки статуса платежа
        payment_id = payment_data.get('payment_id')
        order_id = payment_data.get('order_id')
        
        # Отменяем предыдущую задачу, если она существует
        if user_id in payment_tasks and not payment_tasks[user_id].done():
            payment_tasks[user_id].cancel()
        
        # Создаем новую задачу
        bot = callback.bot
        task = asyncio.create_task(
            check_payment_status_task(user_id, payment_id, order_id, bot, callback.message.chat.id, callback.message.message_id)
        )
        payment_tasks[user_id] = task


@payment_router.callback_query(F.data.startswith("cancel_payment"))
async def cancel_payment(callback: CallbackQuery):
    """
    Обработчик для отмены платежа
    """
    user_id = callback.from_user.id
    payment_id = callback.data.split('_')[-1]

    logger.info(f"Пользователь {user_id} отменил платеж {payment_id}")
    
    # Отменяем задачу проверки платежа, если она существует
    if user_id in payment_tasks and not payment_tasks[user_id].done():
        payment_tasks[user_id].cancel()
        del payment_tasks[user_id]

    async for session in get_session():
        await delete_unpaid_order(session, payment_id)
    
    # Возвращаемся к информации о доставке
    await callback.answer('Платеж отменен.', show_alert=True)
    await show_cart(callback)


async def check_payment_status_task(user_id: int, payment_id: str, order_id: int, bot: Bot, chat_id: int, message_id: int):
    """
    Задача для периодической проверки статуса платежа
    
    Args:
        user_id: ID пользователя
        payment_id: ID платежа
        order_id: ID заказа
        bot: Экземпляр бота для отправки сообщений
        chat_id: ID чата для отправки сообщений
        message_id: ID сообщения для редактирования
    """
    try:
        # Проверяем статус платежа каждые 15 секунд в течение 15 минут
        for _ in range(60):
            # Получаем статус платежа
            payment_status = await check_payment_status(payment_id)
            
            if not payment_status:
                await asyncio.sleep(15)
                continue

            if payment_status['status'] == "succeeded":
                async for session in get_session():
                    await update_order_payment_status(session, payment_id, payment_status['status'])

                    await clear_cart(session, user_id)
                
                # Отправляем уведомление пользователю
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=f"✅ Оплата прошла успешно!\n\n"
                        f"Номер заказа: {order_id}\n"
                        f"Сумма: {payment_status['amount']} руб.\n\n"
                        f"Спасибо за покупку! Мы свяжемся с вами в ближайшее время.",
                    reply_markup=get_successful_payment_keyboard()
                )
                
                # Удаляем задачу из словаря
                if user_id in payment_tasks:
                    del payment_tasks[user_id]
                
                break
            elif payment_status['status'] in ["canceled", "pending"]:
                # Продолжаем проверять статус
                await asyncio.sleep(15)
                continue
            else:
                async for session in get_session():
                    await update_order_payment_status(session, payment_id, payment_status['status'])
                
                # Отправляем уведомление пользователю
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=f"❌ Платеж не был завершен.\n\n"
                        f"Статус: {payment_status['status']}\n\n"
                        f"Вы можете повторить попытку оплаты.",
                    reply_markup=get_back_to_cart_keyboard()
                )
                
                # Удаляем задачу из словаря
                if user_id in payment_tasks:
                    del payment_tasks[user_id]
                
                break
            
        # Если вышли из цикла по времени (15 минут прошло)
        else:
            payment_status = await check_payment_status(payment_id)
            
            if payment_status and payment_status['status'] == "succeeded":
                async for session in get_session():
                    await update_order_payment_status(session, payment_id, payment_status['status'])
                    await clear_cart(session, user_id)
                
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=f"✅ Оплата прошла успешно!\n\n"
                        f"Номер заказа: {order_id}\n"
                        f"Сумма: {payment_status['amount']} руб.\n\n"
                        f"Спасибо за покупку! Мы свяжемся с вами в ближайшее время.",
                    reply_markup=get_successful_payment_keyboard()
                )
            else:
                # Если платеж не успешен после 15 минут
                async for session in get_session():
                    await delete_unpaid_order(session, payment_id)
                
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=f"⏱ Время ожидания оплаты истекло.\n\n"
                        f"Заказ был отменен. Вы можете создать новый заказ в любое время.",
                    reply_markup=None
                )
            
            # Удаляем задачу из словаря
            if user_id in payment_tasks:
                del payment_tasks[user_id]
    
    except asyncio.CancelledError:
        logger.info(f"Задача проверки платежа для пользователя {user_id} отменена")
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса платежа: {e}")

        if user_id in payment_tasks:
            del payment_tasks[user_id]
