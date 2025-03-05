from sqlalchemy import Column, Integer, String, Text, ForeignKey, Numeric, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from .base import Base


class Order(Base):
    """Модель заказа"""
    __tablename__ = "shop_order"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    username = Column(String(100), nullable=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(Text, nullable=False)
    status = Column(String(20), default="new")
    payment_id = Column(String(100), nullable=True)
    payment_status = Column(String(20), default="pending")
    total_price = Column(Numeric(10, 2), default=0)
    created_at = Column(DateTime, server_default=text("NOW()"))
    updated_at = Column(DateTime, server_default=text("NOW()"), onupdate=text("NOW()"))

    # Отношения
    items = relationship("OrderItem", back_populates="order")

    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, status={self.status})>"


class OrderItem(Base):
    """Модель элемента заказа"""
    __tablename__ = "shop_orderitem"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("shop_order.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("shop_product.id"), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, default=1)

    # Отношения
    order = relationship("Order", back_populates="items")
    product = relationship("Product")

    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product_id={self.product_id})>" 