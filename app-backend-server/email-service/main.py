from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse
from shared.database import users_collection
from send_email import send_booking_email, send_parent_notify_email
from models import TransactionEmailRequest, ParentNotifyEmailRequest

app = FastAPI(
    title="Email Service",
    description="API để gửi email thông báo booking",
    version="1.0.0",
    root_path="/api/email"
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/send-email")
def send_booking_email_api(input: TransactionEmailRequest = Body(...)) -> dict:
    # 1. Kiểm tra applicant có tồn tại trong DB
    user_data = users_collection.find_one({"email": input.applicant_email})
    if not user_data:
        raise HTTPException(
            status_code=404,
            detail="Applicant email not found in users_collection"
        )

    # Tên applicant ưu tiên từ DB
    applicant_name = (
        user_data.get("display_name")
        or input.applicant_name
        or "Applicant"
    )

    # 2. Khởi tạo và gửi email
    success = send_booking_email(
        applicant_email=input.applicant_email,
        applicant_name=applicant_name,
        parent_name=input.parent_name or "",
        post_title=input.post_title or "",
        poster_email=input.poster_email or "",
        poster_phone=input.poster_phone or "",
        content=input.content
    )

    # 3. Trả kết quả
    if success:
        return JSONResponse(
            content={"message": f"Booking email sent to {input.applicant_email}"},
            status_code=200
        )
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to send booking email"
        )





@app.post("/send-parent-notify")
def send_parent_notify_api(input: ParentNotifyEmailRequest = Body(...)) -> dict:
    user_data = users_collection.find_one({"email": input.parent_email})
    if not user_data:
        raise HTTPException(status_code=404, detail="Parent email not found in users_collection")

    parent_name = user_data.get("display_name") or input.parent_name or "Parent"

    success = send_parent_notify_email(input.parent_email, parent_name, input.post_title)

    if success:
        return JSONResponse(content={"message": f"Parent notification sent to {input.parent_email}"}, status_code=200)
    else:
        raise HTTPException(status_code=500, detail="Failed to send parent notification")