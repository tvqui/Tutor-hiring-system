from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime

# ==========================
# USER
# ==========================
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

    @validator("*", pre=True)
    def empty_or_string_to_none(cls, v):
        if v in ("", "string", None):
            return None
        return v

# ==========================
# POST
# ==========================
class PostModel(BaseModel):
    id: Optional[str]  # MongoDB _id sẽ là ObjectId, chuyển sang str
    creator_id: str    # ObjectId của user, chuyển sang str
    title: str
    subject: Optional[str] = None
    level: Optional[str] = None
    address: Optional[str] = None
    salary_amount: Optional[float] = None 
    sessions_per_week: Optional[int] = None
    minutes_per_session: Optional[int] = None
    preferred_times: Optional[str] = None
    student_info: Optional[str] = None
    requirements: Optional[str] = None
    mode: Optional[str] = None  # online, offline, hybrid
    post_status: Optional[str] = None  # Post_Status
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @validator(
        "subject",
        "level",
        "address",
        "salary_amount",
        "sessions_per_week",
        "minutes_per_session",
        "preferred_times",
        "student_info",
        "requirements",
        "mode",
        "post_status",
        "created_at",
        "updated_at",
        pre=True,
    )
    def empty_or_string_to_none(cls, v):
        if v in ("", "string", None):
            return None
        return v

    class Config:
        orm_mode = True

class AddPostModel(BaseModel):
    title: str
    subject: Optional[str] = None
    level: Optional[str] = None
    address: Optional[str] = None
    salary_amount: Optional[float] = None 
    sessions_per_week: Optional[int] = None
    minutes_per_session: Optional[int] = None
    preferred_times: Optional[str] = None
    student_info: Optional[str] = None
    requirements: Optional[str] = None
    mode: Optional[str] = None 
    post_status: Optional[str] = None

    @validator(
        "subject",
        "level",
        "address",
        "salary_amount",
        "sessions_per_week",
        "minutes_per_session",
        "preferred_times",
        "student_info",
        "requirements",
        "mode",
        "post_status",
        pre=True,
    )
    def empty_or_string_to_none(cls, v):
        if v in ("", "string", None):
            return None
        return v

class DelPostModel(BaseModel):
    id: str
