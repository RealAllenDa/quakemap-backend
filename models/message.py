from sqlalchemy import Column, String, Integer, DateTime, func

from .base import Base


class DbMessages(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String)
    event_id = Column(Integer, index=True)
    serial = Column(Integer)
    event_time = Column(DateTime)
    store_time = Column(DateTime, server_default=func.now())
    data = Column(String)
