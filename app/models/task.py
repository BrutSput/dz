from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship

from app.core.db import Base


class Task(Base):
    name = Column(String, nullable=False)
    text_of_task = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    created_at = Column(DateTime, autoincrement=True)
    close = Column(DateTime)
    user = relationship('User', back_populates='reservations')

