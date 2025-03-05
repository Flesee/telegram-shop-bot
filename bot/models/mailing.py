from sqlalchemy import Column, Integer, Text, Boolean, DateTime, func

from .base import Base


class Mailing(Base):
    """Модель рассылки"""
    __tablename__ = "shop_mailing"
    
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    is_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Mailing(id={self.id}, scheduled_at={self.scheduled_at})>"
