from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key= True, index= True)
    email = Column(String, unique= True)
    password = Column(String)

    is_admin = Column(Boolean, default=False)

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key= True, index= True)
    title = Column(String)
    date = Column(String)
    location = Column(String)
    price = Column(String)

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key= True, index= True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_id = Column(Integer, ForeignKey("events.id"))

    owner = relationship("User")
    event = relationship("Event")