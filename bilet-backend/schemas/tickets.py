from pydantic import BaseModel

from schemas.events import EventSchema


class TicketTransferSchema(BaseModel):
    id: int
    target_email: str


class TicketResponse(BaseModel):
    id: int
    user_id: int
    event_id: int

    event: EventSchema

    class Config:
        from_attributes = True
