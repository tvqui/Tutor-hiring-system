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

class TransactionModel(BaseModel):
    id: str
    post_id: str
    payer_id: str
    amount_money: float
    transaction_status: Optional[str] = None
    created_at: Optional[datetime]

    @validator("transaction_status", "created_at", pre=True)
    def empty_string_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v

class AddTransactionModel(BaseModel):
    post_id: str
    amount_money: float


class AddApplicationPaymentModel(BaseModel):
    application_id: str
    amount_money: float
    post_id: Optional[str] = None