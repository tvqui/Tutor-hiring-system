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
# APPLICATION
# ==========================
class ApplicationModel(BaseModel):
    id: str
    post_id: str
    tutor_id: str
    application_status: Optional[str] = None
    applied_at: Optional[datetime] = None

    @validator("application_status", pre=True)
    def status_empty_or_string_to_none(cls, v):
        if v in ("", "string", None):
            return None
        return v

    @validator("applied_at", pre=True)
    def datetime_empty_or_string_to_none(cls, v):
        if v in ("", "string", None):
            return None
        return v

class GetApplicationModel(BaseModel):
    post_id: str

class AddApplicationModel(BaseModel):
    post_id: str

class DeleteApplicationModel(BaseModel):
    id: str

class UpdateApplicationModel(BaseModel):
    id: str
    application_status: Optional[str] = None

    @validator("application_status", pre=True)
    def update_status_empty_or_string_to_none(cls, v):
        if v in ("", "string", None):
            return None
        return v