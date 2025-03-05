from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from models import FAQ


def get_faq_keyboard(faqs: list[FAQ]) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру со списком FAQ
    """
    builder = InlineKeyboardBuilder()
    
    for faq in faqs:
        builder.button(
            text=faq.question[:50] + ("..." if len(faq.question) > 50 else ""),
            callback_data=f"faq:{faq.id}"
        )

    builder.button(text="🏠 Главное меню", callback_data="start")
    
    builder.adjust(1)
    
    return builder.as_markup()


def get_faq_detail_keyboard(faq_id: int) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для детального просмотра FAQ
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(text="⬅️ Назад к списку вопросов", callback_data="faq_list")
    builder.button(text="🏠 Главное меню", callback_data="start")
    
    builder.adjust(1)
    
    return builder.as_markup()


def get_faq_search_results_keyboard(faqs: list[FAQ]) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с результатами поиска FAQ
    """
    builder = InlineKeyboardBuilder()
    
    if faqs:
        for faq in faqs:
            builder.button(
                text=faq.question[:50] + ("..." if len(faq.question) > 50 else ""),
                callback_data=f"faq:{faq.id}"
            )
    else:
        builder.button(text="❌ Ничего не найдено", callback_data="faq_list")
    
    builder.button(text="⬅️ Назад к списку вопросов", callback_data="faq_list")
    builder.button(text="🏠 Главное меню", callback_data="start")
    
    builder.adjust(1)
    
    return builder.as_markup()
