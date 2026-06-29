from typing import Literal, Optional

from pydantic import BaseModel


class AISearchRequest(BaseModel):
    prompt: str


class AIChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AIChatFilters(BaseModel):
    city: Optional[str] = None
    category: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class AIChatSlotState(BaseModel):
    category: Literal["unknown", "filled", "any"] = "unknown"
    city: Literal["unknown", "filled", "any"] = "unknown"
    date: Literal["unknown", "filled", "any"] = "unknown"
    requested_slot: Optional[Literal["category", "city", "date"]] = None


class AIChatRequest(BaseModel):
    messages: list[AIChatMessage]
    current_filters: Optional[AIChatFilters] = None
    slot_state: Optional[AIChatSlotState] = None
