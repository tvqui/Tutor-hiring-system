from pydantic import BaseModel, Field
from typing import Optional


class TransactionEmailRequest(BaseModel):
    applicant_email: str = Field(..., description="Email of the applicant receiving the confirmation")
    applicant_name: Optional[str] = Field(None, description="Full name of the applicant")
    parent_name: Optional[str] = Field(None, description="Full name of the parent/tutor approving")
    
    post_title: Optional[str] = Field(None, description="Title of the post being booked")
    poster_email: Optional[str] = Field(None, description="Email of the tutor/post owner")
    poster_phone: Optional[str] = Field(None, description="Phone number of the tutor/post owner")

    content: str = Field(..., description="Message content of the booking confirmation")


# class TutorSelectedEmailRequest(BaseModel):
#     tutor_email: str = Field(..., description="Email of the tutor being selected")
#     tutor_name: Optional[str] = Field(None, description="Tutor full name")
#     post_title: str = Field(..., description="Title of the post they were selected for")


class ParentNotifyEmailRequest(BaseModel):
    parent_email: str = Field(..., description="Email of the post owner / parent")
    parent_name: Optional[str] = Field(None, description="Parent full name")
    post_title: str = Field(..., description="Title of the post")