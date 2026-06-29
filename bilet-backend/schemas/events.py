from typing import Optional

from pydantic import BaseModel


class EventCreate(BaseModel):
    title: str
    date: str
    location: str
    price: str
    description: str
    image: Optional[str] = None
    city: str
    category: str
    capacity: int
    time: str


class EventSchema(BaseModel):
    id: int
    title: str
    date: str
    location: str
    price: str
    description: str
    image: Optional[str] = None
    city: str
    category: str
    capacity: int
    available_tickets: int
    time: str

    class Config:
        from_attributes = True
