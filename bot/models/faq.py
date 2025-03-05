from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import text
from .base import Base


class FAQ(Base):
    """Модель часто задаваемых вопросов"""
    __tablename__ = "shop_faq"

    id = Column(Integer, primary_key=True)
    question = Column(String(255), unique=True, nullable=False)
    answer = Column(Text, nullable=False)
    keywords = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=text("NOW()"))
    updated_at = Column(DateTime, server_default=text("NOW()"), onupdate=text("NOW()"))

    def __repr__(self):
        return f"<FAQ(id={self.id}, question={self.question[:30]}...)>" 