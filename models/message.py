from sqlalchemy import Column, String, Integer, DateTime, func, JSON

from .base import Base


class DbMessages(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String)
    event_id = Column(String, index=True)
    serial = Column(Integer)
    event_time = Column(DateTime(timezone=True))
    store_time = Column(DateTime(timezone=True), server_default=func.now())
    data = Column(JSON)
