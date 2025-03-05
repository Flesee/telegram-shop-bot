from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Mailing
from services.user_service import get_all_users


async def get_pending_mailings(session: AsyncSession) -> list[Mailing]:
    """Получить все неотправленные рассылки, время которых уже наступило"""
    query = select(Mailing).where(
        Mailing.is_sent == False,
        Mailing.scheduled_at <= datetime.now()
    )
    result = await session.execute(query)
    return list(result.scalars().all())


async def mark_mailing_as_sent(session: AsyncSession, mailing_id: int) -> None:
    """Отметить рассылку как отправленную"""
    mailing = await session.get(Mailing, mailing_id)
    if mailing:
        mailing.is_sent = True
        await session.commit()


async def process_mailings(bot) -> None:
    """Обработать все ожидающие рассылки"""
    from database import get_session
    
    async for session in get_session():
        # Получаем все неотправленные рассылки
        mailings = await get_pending_mailings(session)
        
        if not mailings:
            return

        users = await get_all_users(session)
        
        # Отправляем каждую рассылку
        for mailing in mailings:
            for user in users:
                try:
                    await bot.send_message(
                        chat_id=user.user_id,
                        text=mailing.text
                    )
                except Exception as e:
                    print(f"Ошибка отправки сообщения пользователю {user.user_id}: {e}")
            
            # Отмечаем рассылку как отправленную
            await mark_mailing_as_sent(session, mailing.id)
