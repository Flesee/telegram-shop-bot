from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Numeric, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from .base import Base


class Category(Base):
    """Модель категории товаров"""
    __tablename__ = "shop_category"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("shop_category.id"), nullable=True)
    created_at = Column(DateTime, server_default=text("NOW()"))
    updated_at = Column(DateTime, server_default=text("NOW()"), onupdate=text("NOW()"))
    
    # Отношения
    products = relationship("Product", back_populates="category")
    subcategories = relationship("Category", backref="parent", remote_side=[id])
    
    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name})>"


class Product(Base):
    """Модель товара"""
    __tablename__ = "shop_product"
    
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("shop_category.id"), nullable=False)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    image = Column(String(255), nullable=True)
    available = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=text("NOW()"))
    updated_at = Column(DateTime, server_default=text("NOW()"), onupdate=text("NOW()"))
    
    # Отношения
    category = relationship("Category", back_populates="products")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, price={self.price})>" 