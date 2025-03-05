from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from database import get_session
from services.user_service import get_or_create_user
from utils.logger import logger
from keyboards import get_main_keyboard
from config import CHANNEL_ID

start_router = Router()


@start_router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name
    
    logger.info(f"Пользователь {user_id} (@{username}, {full_name}) запустил бота")

    async for session in get_session():
        await get_or_create_user(session, user_id, username)
    
    await message.answer(
        f"👋 Привет, {full_name}!\n\n"
        "Добро пожаловать в наш магазин",
        reply_markup=get_main_keyboard()
    )


@start_router.callback_query(F.data == "start")
async def callback_start(callback: CallbackQuery):
    """Обработчик callback-запроса start"""
    user_id = callback.from_user.id
    username = callback.from_user.username
    full_name = callback.from_user.full_name
    
    logger.info(f"Пользователь {user_id} (@{username}, {full_name}) вернулся в главное меню")

    await callback.message.edit_text(
        f"👋 Привет, {full_name}!\n\n"
        "Добро пожаловать в наш магазин",
        reply_markup=get_main_keyboard()
    )


@start_router.callback_query(F.data == "check_subscription")
async def check_subscription(callback: CallbackQuery):
    """Обработчик проверки подписки на канал"""
    user_id = callback.from_user.id
    full_name = callback.from_user.full_name
    
    # Проверяем, подписан ли пользователь на канал
    user_channel_status = await callback.bot.get_chat_member(CHANNEL_ID, user_id)
    
    if user_channel_status.status in ['member', 'administrator', 'creator']:
        await callback.answer("✅ Спасибо за подписку!")
        await callback.message.edit_text(
            f"👋 Привет, {full_name}!\n\n"
            "Добро пожаловать в наш магазин",
            reply_markup=get_main_keyboard()
        )
        logger.info(f"Пользователь {user_id} подписался на канал")
    else:

        await callback.answer(
            "❌ Вы не подписаны на канал. Пожалуйста, подпишитесь для продолжения.",
            show_alert=True
        )
        logger.info(f"Пользователь {user_id} не подписался на канал")
