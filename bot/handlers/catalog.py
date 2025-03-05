from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from pathlib import Path

from database import get_session
from services.product_service import (
    get_main_categories, get_subcategories, get_category_by_id, 
    get_products_by_category, get_product_by_id, count_products_in_category,
    count_main_categories, count_subcategories
)
from services.cart_service import add_to_cart
from utils.logger import logger
from utils.formatters import format_price, format_total_price
from keyboards import get_categories_keyboard, get_products_keyboard, get_product_keyboard, get_product_added_keyboard

catalog_router = Router()

# Количество товаров на одной странице
ITEMS_PER_PAGE = 10


@catalog_router.callback_query(F.data == "catalog")
async def show_catalog(callback: CallbackQuery):
    """Показать каталог основных категорий"""
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} открыл каталог")

    await show_main_categories_page(callback, page=1)


async def show_main_categories_page(callback: CallbackQuery, page: int):
    """Вспомогательная функция для показа основных категорий с указанной страницей"""
    user_id = callback.from_user.id
    
    logger.info(f"Пользователь {user_id} просматривает основные категории, страница {page}")
    
    async for session in get_session():
        categories = await get_main_categories(session, page, ITEMS_PER_PAGE)
        
        # Получаем общее количество категорий для расчета страниц
        total_categories = await count_main_categories(session)
        total_pages = (total_categories + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        
        if not categories:
            await callback.answer("😔 В каталоге пока нет категорий.", show_alert=True)
            return
        
        await callback.message.edit_text(
            "🛍️ Каталог товаров\n\n"
            "Выберите категорию:",
            reply_markup=get_categories_keyboard(categories, is_main=True, current_page=page, total_pages=total_pages)
        )
    
    await callback.answer()


@catalog_router.callback_query(F.data.startswith("main_categories_"))
async def show_main_categories(callback: CallbackQuery):
    """Показать основные категории с пагинацией"""
    page = int(callback.data.split("_")[2])
    await show_main_categories_page(callback, page)


@catalog_router.callback_query(F.data.startswith("main_category_"))
async def show_subcategories(callback: CallbackQuery):
    """Показать подкатегории выбранной основной категории"""
    category_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    logger.info(f"Пользователь {user_id} открыл основную категорию {category_id}")

    await show_subcategories_page_with_params(callback, parent_id=category_id, page=1)


async def show_subcategories_page_with_params(callback: CallbackQuery, parent_id: int, page: int):
    """Вспомогательная функция для показа подкатегорий с указанными параметрами"""
    user_id = callback.from_user.id
    
    logger.info(f"Пользователь {user_id} просматривает подкатегории категории {parent_id}, страница {page}")
    
    async for session in get_session():
        category = await get_category_by_id(session, parent_id)
        
        subcategories = await get_subcategories(session, parent_id, page, ITEMS_PER_PAGE)
        
        # Получаем общее количество подкатегорий для расчета страниц
        total_subcategories = await count_subcategories(session, parent_id)
        total_pages = (total_subcategories + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        
        if not subcategories:
            # Если подкатегорий нет, показываем товары этой категории
            logger.info(f"Подкатегории не найдены для категории {parent_id}, показываем товары")
            await show_products_with_params(callback, parent_id, 1)
            return
        
        await callback.message.edit_text(
            f"📂 Категория: {category.name}\n\n"
            f"Выберите подкатегорию:",
            reply_markup=get_categories_keyboard(subcategories, is_main=False, current_page=page, total_pages=total_pages, parent_id=parent_id)
        )
    
    await callback.answer()


@catalog_router.callback_query(F.data.startswith("subcategories_"))
async def show_subcategories_page(callback: CallbackQuery):
    """Показать подкатегории с пагинацией"""
    parts = callback.data.split("_")
    parent_id = int(parts[1])
    page = int(parts[2])
    
    await show_subcategories_page_with_params(callback, parent_id, page)


@catalog_router.callback_query(F.data.startswith("category_"))
async def show_products(callback: CallbackQuery, state: FSMContext):
    """Показать товары выбранной категории"""
    data = await state.get_data()
    message_photo = data.get('message_photo')
    if message_photo:
        await message_photo.delete()
        await state.clear()
    parts = callback.data.split("_")
    category_id = int(parts[1])
    page = int(parts[2]) if len(parts) > 2 else 1
    
    await show_products_with_params(callback, category_id, page)


@catalog_router.callback_query(F.data.startswith("product_"))
async def show_product(callback: CallbackQuery, state: FSMContext):
    """Показать детали товара"""
    product_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    logger.info(f"Пользователь {user_id} открыл товар {product_id}")
    
    async for session in get_session():
        product = await get_product_by_id(session, product_id)
        
        if not product:
            await callback.answer("Товар не найден", show_alert=True)
            return
        
        # Форматируем цену для лучшего отображения
        price_str = format_price(product.price)
        
        message_text = (
            f"🛍️ {product.name}\n\n"
            f"{product.description}\n\n"
            f"💰 Цена: {price_str}"
        )

        # Если у товара есть изображение
        if product.image:
            image_path = Path("/media") / str(product.image)

            await callback.message.delete()
            
            if image_path.exists():
                message_photo = await callback.message.answer_photo(
                    photo=FSInputFile(image_path),
                )
                await state.update_data(message_photo=message_photo)

                await callback.message.answer(
                    text=message_text,
                    reply_markup=get_product_keyboard(product)
                )
            else:
                await callback.message.edit_text(
                text=message_text,
                reply_markup=get_product_keyboard(product)
            )
        else:
            await callback.message.edit_text(
                text=message_text,
                reply_markup=get_product_keyboard(product)
            )
    
    await callback.answer()


@catalog_router.callback_query(F.data.startswith("change_quantity_"))
async def change_product_quantity(callback: CallbackQuery):
    """Изменить количество товара"""
    parts = callback.data.split("_")
    product_id = int(parts[2])
    quantity = int(parts[3])
    user_id = callback.from_user.id
    
    logger.info(f"Пользователь {user_id} изменил количество товара {product_id} на {quantity}")
    
    async for session in get_session():
        product = await get_product_by_id(session, product_id)
        
        if not product:
            await callback.answer("Товар не найден", show_alert=True)
            return
        
        # Форматируем цену и общую стоимость
        price_str, total_price_str = format_total_price(product.price, quantity)
        
        message_text = (
            f"🛍️ {product.name}\n\n"
            f"{product.description}\n\n"
            f"💰 Цена: {price_str}\n"
        )
        
        # Добавляем информацию об общей стоимости, если количество больше 1
        if quantity > 1:
            message_text += f"💵 Общая стоимость: {total_price_str}\n"
        
        # Обновляем сообщение с новым количеством
        await callback.message.edit_text(
            text=message_text,
            reply_markup=get_product_keyboard(product, quantity)
        )
    
    await callback.answer()


@catalog_router.callback_query(F.data.startswith("confirm_add_to_cart_"))
async def confirm_add_to_cart(callback: CallbackQuery, state: FSMContext):
    """Подтверждение добавления товара в корзину"""
    data = await state.get_data()
    message_photo = data.get('message_photo')
    if message_photo:
        await message_photo.delete()
        await state.clear()
    parts = callback.data.split("_")
    product_id = int(parts[4])
    quantity = int(parts[5]) if len(parts) > 5 else 1
    user_id = callback.from_user.id
    
    logger.info(f"Пользователь {user_id} подтверждает добавление товара {product_id} в корзину в количестве {quantity}")
    
    async for session in get_session():
        product = await get_product_by_id(session, product_id)
        
        if not product:
            await callback.answer("Товар не найден", show_alert=True)
            return
        
        # Форматируем цену и общую стоимость
        price_str, total_price_str = format_total_price(product.price, quantity)
        
        message_text = (
            f"🛍️ {product.name}\n\n"
            f"Количество: {quantity} шт.\n"
            f"Цена за единицу: {price_str}\n"
            f"Общая стоимость: {price_str.replace(' руб.', '')} × {quantity} = {total_price_str}\n\n"
            f"Добавить товар в корзину?"
        )
        
        builder = InlineKeyboardBuilder()
        builder.button(
            text="✅ Добавить",
            callback_data=f"add_to_cart_{product.id}_{quantity}"
        )
        builder.button(
            text="❌ Отмена",
            callback_data=f"product_{product.id}"
        )
        builder.adjust(1)
        
        await callback.message.edit_text(
            text=message_text,
            reply_markup=builder.as_markup()
        )
    
    await callback.answer()


@catalog_router.callback_query(F.data.startswith("add_to_cart_"))
async def add_product_to_cart(callback: CallbackQuery):
    """Добавить товар в корзину"""
    parts = callback.data.split("_")
    product_id = int(parts[3])
    quantity = int(parts[4]) if len(parts) > 4 else 1
    user_id = callback.from_user.id
    
    logger.info(f"Пользователь {user_id} добавляет товар {product_id} в корзину в количестве {quantity}")
    
    async for session in get_session():
        product = await get_product_by_id(session, product_id)
        
        if not product:
            await callback.answer("Товар не найден", show_alert=True)
            return
        
        # Добавляем товар в корзину с указанным количеством
        await add_to_cart(session, user_id, product_id, quantity)
        
        await callback.answer(f"✅ Товар '{product.name}' добавлен в корзину в количестве {quantity} шт.!")
        
        # Форматируем цену и общую стоимость
        price_str, total_price_str = format_total_price(product.price, quantity)
        
        message_text = (
            f"✅ Товар добавлен в корзину!\n\n"
            f"🛍️ {product.name}\n"
            f"Количество: {quantity} шт.\n"
            f"Цена за единицу: {price_str}\n"
            f"Общая стоимость: {price_str.replace(' руб.', '')} × {quantity} = {total_price_str}"
        )
        
        await callback.message.edit_text(
            text=message_text,
            reply_markup=get_product_added_keyboard(product)
        )


@catalog_router.callback_query(F.data == "back_to_main_categories")
async def back_to_main_categories(callback: CallbackQuery):
    """Вернуться к списку основных категорий"""
    user_id = callback.from_user.id
    
    logger.info(f"Пользователь {user_id} возвращается к списку основных категорий")
    
    await show_main_categories_page(callback, page=1)


@catalog_router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    """Вернуться к списку подкатегорий"""
    user_id = callback.from_user.id
    
    logger.info(f"Пользователь {user_id} возвращается к списку категорий")
    
    await show_main_categories_page(callback, page=1)


@catalog_router.callback_query(F.data.startswith("back_to_category_"))
async def back_to_category(callback: CallbackQuery):
    """Вернуться к списку товаров в категории"""
    category_id = int(callback.data.split("_")[3])
    user_id = callback.from_user.id
    
    logger.info(f"Пользователь {user_id} возвращается к категории {category_id}")

    await show_products_with_params(callback, category_id, page=1)


async def show_products_with_params(callback: CallbackQuery, category_id: int, page: int):
    """Вспомогательная функция для показа товаров с указанными параметрами"""
    user_id = callback.from_user.id
    
    logger.info(f"Пользователь {user_id} открыл категорию {category_id}, страница {page}")
    
    async for session in get_session():
        category = await get_category_by_id(session, category_id)
        
        # Получаем товары для текущей страницы
        products = await get_products_by_category(session, category_id, page, ITEMS_PER_PAGE)
        
        # Получаем общее количество товаров для расчета страниц
        total_products = await count_products_in_category(session, category_id)
        total_pages = (total_products + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        
        if not products:
            await callback.answer("В этой категории пока нет товаров", show_alert=True)
            return
        
        await callback.message.edit_text(
            f"📂 Категория: {category.name}\n\n"
            f"Выберите товар:",
            reply_markup=get_products_keyboard(products, category_id, page, total_pages)
        )
    
    await callback.answer()


@catalog_router.callback_query(F.data == "empty")
async def handle_empty_button(callback: CallbackQuery):
    """Обработка нажатия на пустую кнопку"""
    await callback.answer("Это информационная кнопка")


@catalog_router.callback_query(F.data.startswith("back_to_parent_category_"))
async def back_to_parent_category(callback: CallbackQuery):
    """Вернуться к родительской категории"""
    category_id = int(callback.data.split("_")[4])
    user_id = callback.from_user.id
    
    logger.info(f"Пользователь {user_id} возвращается из категории {category_id} к родительской категории")
    
    async for session in get_session():
        category = await get_category_by_id(session, category_id)
        
        if not category:
            await callback.answer("Категория не найдена", show_alert=True)
            return
        
        # Если у категории есть родитель, возвращаемся к нему
        if category.parent_id:
            parent_id = category.parent_id
            await get_category_by_id(session, parent_id)

            await show_subcategories_page_with_params(callback, parent_id=parent_id, page=1)
        else:
            # Если у категории нет родителя, возвращаемся к списку основных категорий
            await show_main_categories_page(callback, page=1)
    
    await callback.answer()
