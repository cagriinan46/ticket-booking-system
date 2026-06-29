from sqlalchemy import Column, ForeignKey, Integer, Table

from database import Base


favorite_events = Table(
    "favorite_events",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("event_id", Integer, ForeignKey("events.id"), primary_key=True)
)
