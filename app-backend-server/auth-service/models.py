from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime


# ===============================
#  HÀM XỬ LÝ GIÁ TRỊ (CHUNG)
# ===============================

def normalize_value(value):
    """
    Chuẩn hoá giá trị:
    - "string"  -> None
    - ""        -> None
    - List      -> normalize từng phần tử
    """
    if value in ["", "string"]:
        return None

    if isinstance(value, list):
        return [normalize_value(v) for v in value]

    return value


# ===============================
#  TOKEN + AUTH MODELS
# ===============================

class TokenModel(BaseModel):
    access_token: str
    token_type: str


class LoginModel(BaseModel):
    username: str
    password: str


# ===============================
#  FULL USER MODEL (response login)
# ===============================

class UserModel(BaseModel):
    id: str
    username: str
    email: str
    phone: Optional[str] = None
    password_hash: str

    # Role of the user: 'customer' or 'admin'
    role: Optional[str] = None
    # Verification/status for profile: unverified|pending|rejected|accepted
    status: Optional[str] = None

    display_name: Optional[str] = None
    subjects: Optional[List[str]] = None
    levels: Optional[List[str]] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    bio: Optional[str] = None
    avg_rating: Optional[float] = None
    rating_count: Optional[int] = 0


# ===============================
#  PROFILE MODEL (public profile)
# ===============================

class ProfileModel(BaseModel):
    id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    display_name: Optional[str] = None
    subjects: Optional[List[str]] = None
    levels: Optional[List[str]] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    bio: Optional[str] = None
    avg_rating: Optional[float] = None
    rating_count: Optional[int] = 0
    role: Optional[str] = None
    status: Optional[str] = None

    @validator("*", pre=True)
    def normalize(cls, v):
        return normalize_value(v)


# ===============================
#  UPDATE PROFILE MODEL
# ===============================

class UpdateProfileModel(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    display_name: Optional[str] = None
    subjects: Optional[List[str]] = None
    levels: Optional[List[str]] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    bio: Optional[str] = None

    @validator("*", pre=True)
    def normalize(cls, v):
        return normalize_value(v)


# ===============================
#  CERTIFICATE MODELS
# ===============================

class CertificateModel(BaseModel):
    id: str
    certificate_type: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    filename: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True

    @validator("*", pre=True)
    def empty_string_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class AddCertificateModel(BaseModel):
    certificate_type: str
    description: Optional[str] = None
    url: Optional[str] = None
    filename: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    status: Optional[str] = None

    @validator("*", pre=True)
    def normalize(cls, v):
        return normalize_value(v)


class DelCertificateModel(BaseModel):
    id: str


# ===============================
#  GET BY USER ID MODELS
# ===============================

class GetProfileByUserIDModel(BaseModel):
    user_id: str

    @validator("user_id", pre=True)
    def normalize_user_id(cls, v):
        return normalize_value(v)


class GetCertificateByUserIDModel(BaseModel):
    user_id: str

    @validator("user_id", pre=True)
    def normalize_user_id(cls, v):
        return normalize_value(v)


class UpdateProfileStatusModel(BaseModel):
    user_id: str
    status: str

    @validator('user_id', pre=True)
    def normalize_user_id(cls, v):
        return normalize_value(v)


class UpdateCertificateStatusModel(BaseModel):
    certificate_id: str
    status: str

    @validator('certificate_id', pre=True)
    def normalize_certificate_id(cls, v):
        return normalize_value(v)


class ProofImageModel(BaseModel):
    id: str
    type: str  # 'profile' or 'certificate'
    type_id: str
    image: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AddProofImageModel(BaseModel):
    type: str
    type_id: str
    image: str

    @validator('type', pre=True)
    def normalize_type(cls, v):
        return normalize_value(v)


class DelProofImageModel(BaseModel):
    id: str

    @validator('id', pre=True)
    def normalize_id(cls, v):
        return normalize_value(v)