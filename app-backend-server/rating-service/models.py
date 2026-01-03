from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RatingModel(BaseModel):
    id: str
    tutor_id: str
    parent_id: str
    booking_id: Optional[str] = None
    rating: int
    comment: Optional[str] = None
    rated_at: Optional[datetime] = None


class AddRatingModel(BaseModel):
    tutor_id: str
    booking_id: Optional[str] = None
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class UpdateRatingModel(BaseModel):
    id: str
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None


class DelRatingModel(BaseModel):
    id: str
