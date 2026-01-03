from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime

class UserModel(BaseModel):
    id: str
    username: str
    email: str
    phone: Optional[str] = None
    password_hash: str
    display_name: Optional[str] = None
    subjects: Optional[List[str]] = None   
    levels: Optional[List[str]] = None     
    gender: Optional[str] = None
    address: Optional[str] = None
    bio: Optional[str] = None

class BookingModel(BaseModel):
    id: str
    post_id: str
    tutor_id: str
    parent_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    contract_status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @validator("start_date", "end_date", "created_at", "updated_at", pre=True)
    def empty_string_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v

class GetBookingModelByPost(BaseModel):
    post_id: str

class AddBookingModel(BaseModel):
    post_id: str
    tutor_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    contract_status: Optional[str] = None

    @validator("start_date", "end_date", pre=True)
    def parse_datetime(cls, v):
        if v in ("", "string", None):
            return None
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except Exception:
                return None
        return v

    @validator("contract_status", pre=True)
    def fix_contract_status(cls, v):
        if v in ("", "string", None):
            return "accepted"
        return v


class UpdateBookingStatusModel(BaseModel):
    id: str
    contract_status: str
