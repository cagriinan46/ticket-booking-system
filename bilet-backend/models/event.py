from sqlalchemy import Column, Integer, String

from database import Base


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    date = Column(String)
    location = Column(String)
    price = Column(String)
    description = Column(String, nullable=True)
    image = Column(String, nullable=True)
    city = Column(String)
    category = Column(String)
    capacity = Column(Integer)
    time = Column(String)
