from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from database import Base
from models.associations import favorite_events


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    email = Column(String, unique=True)
    password = Column(String)
    email_notifications = Column(Boolean, default=True)

    is_admin = Column(Boolean, default=False)

    favorite_events = relationship("Event", secondary=favorite_events, backref="favorited_by")
