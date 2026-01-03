from typing import List, Optional
from fastapi import FastAPI, HTTPException, Security, status, Query, Body
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId
from datetime import datetime, timezone, timedelta
import requests

from shared.database import users_collection, bookings_collection, posts_collection
# from shared.config import EMAIL_SERVICE_URL
from models import BookingModel, GetBookingModelByPost, AddBookingModel
from jwt_utils import get_current_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
VN_TZ = timezone(timedelta(hours=7))

app = FastAPI(
    title="Booking Service",
    description="API cho booking",
    version="1.0.0",
    root_path="/api/booking"
)


# ==========================
# UPDATE BOOKING STATUS
# ==========================
@app.post(
    "/update-status",
    status_code=status.HTTP_200_OK,
    tags=["Booking"]
)
async def update_booking_status(
    token: str = Security(oauth2_scheme),
    input_data = Body(...)
):
    # input_data expected to be dict with 'id' and 'contract_status'
    current_user = await get_current_user(token, users_collection)
    try:
        bid = ObjectId(input_data.get('id'))
    except Exception:
        raise HTTPException(status_code=400, detail='Invalid booking id')

    b = bookings_collection.find_one({'_id': bid})
    if not b:
        raise HTTPException(status_code=404, detail='Booking not found')

    user_id = str(current_user.id)
    # only parent or tutor involved can change status
    if user_id not in [str(b.get('parent_id')), str(b.get('tutor_id'))]:
        raise HTTPException(status_code=403, detail='Not allowed to update this booking')

    new_status = input_data.get('contract_status')
    if not new_status:
        raise HTTPException(status_code=400, detail='contract_status is required')

    # set updated_at
    bookings_collection.update_one({'_id': bid}, {'$set': {'contract_status': new_status, 'updated_at': datetime.now(VN_TZ)}})
    updated = bookings_collection.find_one({'_id': bid})

    return BookingModel(
        id=str(updated["_id"]),
        post_id=str(updated["post_id"]),
        tutor_id=str(updated["tutor_id"]),
        parent_id=str(updated["parent_id"]),
        start_date=updated.get("start_date"),
        end_date=updated.get("end_date"),
        contract_status=updated.get("contract_status"),
        created_at=updated.get("created_at"),
        updated_at=updated.get("updated_at")
    )

# ==========================
# GET BOOKINGS CỦA NGƯỜI DÙNG
# ==========================
@app.get(
    "/me/get-booking",
    status_code=status.HTTP_200_OK,
    tags=["Booking"],
    response_model=List[BookingModel]
)
async def get_me_bookings(
    token: str = Security(oauth2_scheme),
    scope: Optional[str] = Query("tutor", description="Select 'tutor' or 'parent'"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1)
):
    current_user = await get_current_user(token, users_collection)
    user_id = str(current_user.id)

    if scope not in ["tutor", "parent"]:
        raise HTTPException(status_code=400, detail="scope phải là 'tutor' hoặc 'parent'")  

    query = {f"{scope}_id": ObjectId(user_id)}
    cursor = bookings_collection.find(query).skip(skip).limit(limit)
    booking_list = list(cursor)

    if not booking_list:
        raise HTTPException(status_code=404, detail="No bookings found")
    
    return [
        BookingModel(
            id=str(b["_id"]),
            post_id=str(b["post_id"]),
            tutor_id=str(b["tutor_id"]),
            parent_id=str(b["parent_id"]),
            start_date=b.get("start_date"),
            end_date=b.get("end_date"),
            contract_status=b.get("contract_status"),
            created_at=b.get("created_at"),
            updated_at=b.get("updated_at")
        ) for b in booking_list
    ]

# ==========================
# GET BOOKINGS THEO POST
# ==========================
@app.post(
    "/get-booking-by-post",
    status_code=status.HTTP_200_OK,
    response_model=List[BookingModel],
    tags=["Booking"]
)
async def get_bookings_by_post(
    token: str = Security(oauth2_scheme),
    input_data: GetBookingModelByPost = Body(...)
):
    current_user = await get_current_user(token, users_collection)

    if not input_data or not input_data.post_id:
        raise HTTPException(status_code=400, detail="post_id is required")
    
    post = posts_collection.find_one({"_id": ObjectId(input_data.post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if str(post["creator_id"]) != str(current_user.id):
        raise HTTPException(status_code=403, detail="You are not allowed to view bookings for this post")

    cursor = bookings_collection.find({"post_id": ObjectId(input_data.post_id)})
    booking_list = list(cursor)

    if not booking_list:
        raise HTTPException(status_code=404, detail="No bookings found for this post_id")

    return [
        BookingModel(
            id=str(b["_id"]),
            post_id=str(b["post_id"]),
            tutor_id=str(b["tutor_id"]),
            parent_id=str(b["parent_id"]),
            start_date=b.get("start_date"),
            end_date=b.get("end_date"),
            contract_status=b.get("contract_status"),
            created_at=b.get("created_at"),
            updated_at=b.get("updated_at")
        ) for b in booking_list
    ]

# ==========================
# ADD BOOKING
# ==========================
@app.post(
    "/add-booking",
    status_code=status.HTTP_201_CREATED,
    response_model=BookingModel,
    tags=["Booking"]
)
async def add_booking(
    token: str = Security(oauth2_scheme),
    input_data: AddBookingModel = Body(...)
):
    current_user = await get_current_user(token, users_collection)
    current_user_id = str(current_user.id)

    # Lấy bài post
    post = posts_collection.find_one({"_id": ObjectId(input_data.post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Kiểm tra quyền tạo booking: chỉ owner của post hoặc admin được phép
    db_user = users_collection.find_one({"_id": ObjectId(current_user_id)})
    is_admin = db_user and db_user.get("role") == "admin"
    post_creator_id = str(post["creator_id"])
    if post_creator_id != current_user_id and not is_admin:
        raise HTTPException(status_code=403, detail="Not allowed to add booking to this post")

    # Validate contract_status
    contract_status = input_data.contract_status
    if not contract_status or contract_status.lower() == "string" or contract_status.strip() == "":
        contract_status = "accepted"

    # Tạo booking
    # The booking's parent should be the original post creator (the parent who posted the job)
    booking_data = {
        "post_id": ObjectId(input_data.post_id),
        "tutor_id": ObjectId(input_data.tutor_id),
        "parent_id": ObjectId(post["creator_id"]),
        "start_date": input_data.start_date or None,
        "end_date": input_data.end_date or None,
        "contract_status": contract_status,
        "created_at": datetime.now(VN_TZ),
        "updated_at": datetime.now(VN_TZ),
    }

    saved = bookings_collection.insert_one(booking_data)
    new_booking = bookings_collection.find_one({"_id": saved.inserted_id})

    # try:
    #     # Lấy thông tin tutor (người nhận email)
    #     tutor_data = users_collection.find_one({"_id": ObjectId(input_data.tutor_id)})
    #     tutor_email = tutor_data.get("email") if tutor_data else None
    #     tutor_name = tutor_data.get("display_name") if tutor_data else None

    #     # Lấy thông tin người đăng bài (poster)
    #     poster_data = users_collection.find_one({"_id": ObjectId(post["creator_id"])})
    #     poster_email = poster_data.get("email") if poster_data else None
    #     poster_phone = poster_data.get("phone") if poster_data else None

    #     if tutor_email:
    #         requests.post(
    #             f"{EMAIL_SERVICE_URL}/send-email",
    #             json={
    #                 "applicant_email": tutor_email,                 # tutor nhận email
    #                 "applicant_name": tutor_name,                   # tên tutor
    #                 "parent_name": poster_data.get("display_name") if poster_data else "",  # parent (post creator)
    #                 "post_title": post.get("title"),                # title bài post
    #                 "poster_email": poster_email,                   # email người đăng bài
    #                 "poster_phone": poster_phone,                   # phone người đăng bài
    #                 "content": "Your application has been approved" # nội dung email
    #             },
    #             timeout=5
    #         )

    # except Exception as e:
    #     print("Failed to send booking email:", e)

    return BookingModel(
        id=str(new_booking["_id"]),
        post_id=str(new_booking["post_id"]),
        tutor_id=str(new_booking["tutor_id"]),
        parent_id=str(new_booking["parent_id"]),
        start_date=new_booking.get("start_date"),
        end_date=new_booking.get("end_date"),
        contract_status=new_booking.get("contract_status"),
        created_at=new_booking.get("created_at"),
        updated_at=new_booking.get("updated_at")
    )

# ==========================
# HEALTH CHECK
# ==========================
@app.get("/health", tags=["System"], status_code=200)
async def health_check():
    return {"status": "ok"}