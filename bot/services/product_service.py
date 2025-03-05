from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from models import Category, Product


async def get_main_categories(session: AsyncSession, page: int = 1, items_per_page: int = 10):
    """Получение всех основных категорий (без родительской категории) с пагинацией"""
    # Вычисляем смещение для пагинации
    offset = (page - 1) * items_per_page
    
    result = await session.execute(
        select(Category)
        .where(Category.parent_id == None)
        .offset(offset)
        .limit(items_per_page)
    )
    return result.scalars().all()


async def count_main_categories(session: AsyncSession):
    """Подсчет общего количества основных категорий"""
    result = await session.execute(
        select(func.count())
        .select_from(Category)
        .where(Category.parent_id == None)
    )
    return result.scalar()


async def get_all_categories(session: AsyncSession):
    """Получение всех категорий"""
    result = await session.execute(select(Category))
    return result.scalars().all()


async def get_subcategories(session: AsyncSession, parent_id: int, page: int = 1, items_per_page: int = 10):
    """Получение всех подкатегорий для указанной родительской категории с пагинацией"""
    # Вычисляем смещение для пагинации
    offset = (page - 1) * items_per_page
    
    result = await session.execute(
        select(Category)
        .where(Category.parent_id == parent_id)
        .offset(offset)
        .limit(items_per_page)
    )
    return result.scalars().all()


async def count_subcategories(session: AsyncSession, parent_id: int):
    """Подсчет общего количества подкатегорий для указанной родительской категории"""
    result = await session.execute(
        select(func.count())
        .select_from(Category)
        .where(Category.parent_id == parent_id)
    )
    return result.scalar()


async def get_category_by_id(session: AsyncSession, category_id: int):
    """Получение категории по ID"""
    result = await session.execute(select(Category).where(Category.id == category_id))
    return result.scalars().first()


async def get_products_by_category(session: AsyncSession, category_id: int, page: int = 1, items_per_page: int = 10):
    """Получение товаров в категории с пагинацией"""
    # Вычисляем смещение для пагинации
    offset = (page - 1) * items_per_page
    
    # Получаем товары с учетом пагинации
    result = await session.execute(
        select(Product)
        .where(Product.category_id == category_id, Product.available == True)
        .offset(offset)
        .limit(items_per_page)
    )
    return result.scalars().all()


async def count_products_in_category(session: AsyncSession, category_id: int):
    """Подсчет общего количества товаров в категории"""
    result = await session.execute(
        select(func.count())
        .select_from(Product)
        .where(Product.category_id == category_id, Product.available == True)
    )
    return result.scalar()


async def get_product_by_id(session: AsyncSession, product_id: int):
    """Получение товара по ID"""
    result = await session.execute(select(Product).where(Product.id == product_id))
    return result.scalars().first()
