from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from aiogram.filters import Command
from database import get_session
from services.faq_service import get_all_faqs, get_faq_by_id, search_faqs
from utils.logger import logger
from keyboards.faq import get_faq_keyboard, get_faq_detail_keyboard, get_faq_search_results_keyboard
import hashlib
import re

faq_router = Router()


@faq_router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    user_id = message.from_user.id
    logger.info(f"Пользователь {user_id} вызвал команду /help")
    
    async for session in get_session():
        faqs = await get_all_faqs(session)
    
    if not faqs:
        await message.answer(
            "В данный момент нет доступных вопросов и ответов.",
            reply_markup=get_faq_keyboard([])
        )
        return
    
    await message.answer(
        "❓ Часто задаваемые вопросы\n\n"
        "Выберите интересующий вас вопрос или воспользуйтесь поиском.",
        reply_markup=get_faq_keyboard(faqs)
    )


@faq_router.callback_query(F.data == "help")
async def show_faq_list(callback: CallbackQuery):
    """Показать список FAQ"""
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} открыл FAQ")
    
    async for session in get_session():
        faqs = await get_all_faqs(session)
    
        if not faqs:
            await callback.message.edit_text(
                "В данный момент нет доступных вопросов и ответов.",
                reply_markup=get_faq_keyboard([])
            )
            return

        await callback.message.edit_text(
            "❓ Часто задаваемые вопросы\n\n"
            "Выберите интересующий вас вопрос:",
            reply_markup=get_faq_keyboard(faqs)
        )


@faq_router.callback_query(F.data == "faq_list")
async def callback_faq_list(callback: CallbackQuery):
    """Обработчик возврата к списку FAQ"""
    await show_faq_list(callback)


@faq_router.callback_query(F.data.startswith("faq:"))
async def show_faq_detail(callback: CallbackQuery):
    """Показать детальную информацию о FAQ"""
    user_id = callback.from_user.id
    faq_id = int(callback.data.split(":")[1])
    
    logger.info(f"Пользователь {user_id} открыл FAQ с ID {faq_id}")
    
    async for session in get_session():
        faq = await get_faq_by_id(session, faq_id)
    
    if not faq:
        await callback.answer("Вопрос не найден", show_alert=True)
        await show_faq_list(callback)
        return
    
    await callback.message.edit_text(
        f"Вопрос: {faq.question}\n\n"
        f"Ответ: {faq.answer}",
        reply_markup=get_faq_detail_keyboard(faq_id)
    )


@faq_router.callback_query(F.data == "faq_search")
async def faq_search_prompt(callback: CallbackQuery):
    """Запрос на поиск по FAQ"""
    await callback.message.edit_text(
        "🔍 Введите текст для поиска по вопросам\n\n"
        "Отправьте сообщение с поисковым запросом или нажмите кнопку ниже, чтобы вернуться к списку вопросов.",
        reply_markup=get_faq_detail_keyboard(0)  # 0 - dummy id
    )


async def search_by_keywords(session, search_query):
    """Вспомогательная функция для поиска по ключевым словам"""
    words = re.findall(r'\b\w{3,}\b', search_query.lower())
    if not words:
        return []
        
    # Ищем по каждому ключевому слову отдельно
    all_results = []
    for word in words:
        if len(word) >= 3:  # Игнорируем слишком короткие слова
            results = await search_faqs(session, word)
            all_results.extend(results)
    
    # Удаляем дубликаты
    unique_faqs = []
    seen_ids = set()
    for faq in all_results:
        if faq.id not in seen_ids:
            unique_faqs.append(faq)
            seen_ids.add(faq.id)
    
    return unique_faqs


@faq_router.message(lambda message: message.text and not message.text.startswith('/'))
async def process_faq_search(message: Message):
    """Обработка поискового запроса по FAQ"""
    user_id = message.from_user.id
    
    # Очищаем текст от HTML-тегов и лишних символов
    search_query = re.sub(r'<[^>]+>', '', message.text.strip())
    
    # Проверяем, не является ли текст полным ответом на вопрос
    if "Вопрос:" in search_query and "Ответ:" in search_query:
        # Извлекаем только вопрос для поиска
        question_match = re.search(r'Вопрос:(.*?)(?:Ответ:|$)', search_query, re.DOTALL)
        if question_match:
            search_query = question_match.group(1).strip()
    
    # Если текст слишком длинный, берем только первые 100 символов для поиска
    if len(search_query) > 100:
        search_query = search_query[:100]
    
    logger.info(f"Пользователь {user_id} выполняет поиск по FAQ: {search_query}")
    
    async for session in get_session():
        faqs = await search_faqs(session, search_query)
        
        # Если ничего не найдено, попробуем поиск по ключевым словам
        if not faqs:
            faqs = await search_by_keywords(session, search_query)
    
    if not faqs:
        await message.answer(
            f"🔍 По запросу \"{search_query}\" ничего не найдено.\n\n"
            "Попробуйте изменить поисковый запрос или выберите вопрос из списка:",
            reply_markup=get_faq_search_results_keyboard([])
        )
        return
    
    await message.answer(
        f"🔍 Результаты поиска по запросу \"{search_query}\":\n\n"
        f"Найдено вопросов: {len(faqs)}",
        reply_markup=get_faq_search_results_keyboard(faqs)
    )


@faq_router.inline_query()
async def inline_faq_search(query: InlineQuery):
    """Обработка inline запросов для поиска по FAQ"""
    search_query = query.query.strip()
    
    if not search_query:
        # Если запрос пустой, возвращаем несколько популярных вопросов
        async for session in get_session():
            faqs = await get_all_faqs(session)
            # Ограничиваем количество результатов
            faqs = faqs[:5] if faqs else []
    else:
        # Ищем по запросу
        async for session in get_session():
            faqs = await search_faqs(session, search_query)
            
            # Если ничего не найдено, попробуем поиск по ключевым словам
            if not faqs and len(search_query) > 3:
                faqs = await search_by_keywords(session, search_query)
                faqs = faqs[:5]  # Ограничиваем количество результатов
    
    # Формируем результаты для inline режима
    results = []
    
    for faq in faqs:
        # Создаем уникальный ID для результата на основе ID вопроса
        result_id = hashlib.md5(f"faq_{faq.id}".encode()).hexdigest()

        # Создаем результат - отправляем вопрос с префиксом
        results.append(
            InlineQueryResultArticle(
                id=result_id,
                title=faq.question,
                description=faq.answer[:100] + "..." if len(faq.answer) > 100 else faq.answer,
                input_message_content=InputTextMessageContent(
                    message_text=f"❓ Вопрос: {faq.question}",
                    parse_mode=None
                )
            )
        )
    
    # Если ничего не найдено, показываем сообщение об этом
    if not results and search_query:
        result_id = hashlib.md5(f"not_found_{search_query}".encode()).hexdigest()
        results.append(
            InlineQueryResultArticle(
                id=result_id,
                title="Ничего не найдено",
                description=f"По запросу '{search_query}' ничего не найдено",
                input_message_content=InputTextMessageContent(
                    message_text=f"По запросу '{search_query}' ничего не найдено в FAQ.",
                    parse_mode=None  # Отключаем парсинг HTML/Markdown
                )
            )
        )
    
    # Отправляем результаты
    await query.answer(results=results, cache_time=300)
