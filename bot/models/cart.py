from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from .base import Base


class CartItem(Base):
    """Модель элемента корзины"""
    __tablename__ = "shop_cartitem"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("shop_user.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("shop_product.id"), nullable=False)
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=text("NOW()"))
    updated_at = Column(DateTime, server_default=text("NOW()"), onupdate=text("NOW()"))

    # Отношения
    user = relationship("User")
    product = relationship("Product")

    def __repr__(self):
        return f"<CartItem(id={self.id}, user_id={self.user_id}, product_id={self.product_id}, quantity={self.quantity})>" 