from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from config import CHANNEL_ID
from utils.logger import logger
from keyboards import get_subscription_keyboard


class SubscriptionMiddleware(BaseMiddleware):
    """
    Middleware для проверки подписки пользователя на канал.
    Если пользователь не подписан, то запрос не будет обработан.
    """
    
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        
        # Если это callback_query с проверкой подписки, пропускаем проверку
        if isinstance(event, CallbackQuery) and event.data == "check_subscription":
            return await handler(event, data)

        # Если CHANNEL_ID не задан, пропускаем проверку
        if not CHANNEL_ID:
            logger.warning("CHANNEL_ID не задан, проверка подписки отключена")
            return await handler(event, data)

        user = event.from_user
        
        # Проверяем подписку
        try:
            chat_member = await data["bot"].get_chat_member(CHANNEL_ID, user.id)
            
            if chat_member.status in ["creator", "administrator", "member"]:
                return await handler(event, data)
            else:
                if isinstance(event, Message):
                    await event.answer(
                        "⚠️ Для использования бота необходимо подписаться на наш канал!\n\n"
                        "Подпишитесь и нажмите кнопку «✅ Проверить подписку»",
                        reply_markup=get_subscription_keyboard()
                    )
                elif isinstance(event, CallbackQuery):
                    await event.message.answer(
                        "⚠️ Для использования бота необходимо подписаться на наш канал!\n\n"
                        "Подпишитесь и нажмите кнопку «✅ Проверить подписку»",
                        reply_markup=get_subscription_keyboard()
                    )
                    await event.answer()
                
                logger.info(f"Пользователь {user.full_name} (@{user.username}, ID: {user.id}) не подписан на канал")
                return None
                
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            logger.error(f"Ошибка при проверке подписки: {e}")
            return await handler(event, data) 