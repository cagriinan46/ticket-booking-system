from typing import Optional

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="a score between 1 and 5")
    comment: Optional[str] = None
