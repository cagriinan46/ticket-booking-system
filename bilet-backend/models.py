from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from database import Base

favorite_events = Table(
    "favorite_events",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("event_id", Integer, ForeignKey("events.id"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key= True, index= True)
    name = Column(String, nullable=True)
    email = Column(String, unique= True)
    password = Column(String)
    email_notifications = Column(Boolean, default=True)

    is_admin = Column(Boolean, default=False)

    favorite_events = relationship("Event", secondary=favorite_events, backref="favorited_by")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key= True, index= True)
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

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key= True, index= True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_id = Column(Integer, ForeignKey("events.id"))

    owner = relationship("User")
    event = relationship("Event")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    rating = Column(Integer)
    comment = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_id = Column(Integer, ForeignKey("events.id"))

    user = relationship("User")
    event = relationship("Event")