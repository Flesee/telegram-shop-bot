from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from models import FAQ
from utils.logger import logger


async def get_all_faqs(session: AsyncSession):
    """Получить все FAQ из базы данных"""
    result = await session.execute(select(FAQ))
    return result.scalars().all()


async def get_faq_by_id(session: AsyncSession, faq_id: int):
    """Получить FAQ по ID"""
    result = await session.execute(select(FAQ).where(FAQ.id == faq_id))
    return result.scalar_one_or_none()


async def search_faqs(session: AsyncSession, query: str):
    """Поиск FAQ по запросу в вопросе, ответе или ключевых словах"""
    query = query.lower()
    result = await session.execute(
        select(FAQ).where(
            or_(
                FAQ.question.ilike(f"%{query}%"),
                FAQ.answer.ilike(f"%{query}%"),
                FAQ.keywords.ilike(f"%{query}%")
            )
        )
    )
    return result.scalars().all()


async def create_faq(session: AsyncSession, question: str, answer: str, keywords: str = None):
    """Создать новый FAQ"""
    faq = FAQ(question=question, answer=answer, keywords=keywords)
    session.add(faq)
    await session.commit()
    logger.info(f"Создан новый FAQ: {question}")
    return faq


async def update_faq(session: AsyncSession, faq_id: int, question: str = None, answer: str = None, keywords: str = None):
    """Обновить существующий FAQ"""
    faq = await get_faq_by_id(session, faq_id)
    if not faq:
        return None
    
    if question:
        faq.question = question
    if answer:
        faq.answer = answer
    if keywords is not None:
        faq.keywords = keywords
    
    await session.commit()
    logger.info(f"Обновлен FAQ с ID {faq_id}")
    return faq


async def delete_faq(session: AsyncSession, faq_id: int):
    """Удалить FAQ"""
    faq = await get_faq_by_id(session, faq_id)
    if not faq:
        return False
    
    await session.delete(faq)
    await session.commit()
    logger.info(f"Удален FAQ с ID {faq_id}")
    return True
