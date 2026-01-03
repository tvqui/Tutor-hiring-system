from typing import List, Optional, Literal
from fastapi import FastAPI, HTTPException, Security, status, Query, Body, status
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId
from datetime import datetime, timezone, timedelta

from shared.database import applications_collection, users_collection, posts_collection
from models import ApplicationModel, GetApplicationModel, AddApplicationModel, DeleteApplicationModel, UpdateApplicationModel
from jwt_utils import get_current_user
import requests
from shared.config import EMAIL_SERVICE_URL

# ==========================
# FASTAPI APP
# ==========================
app = FastAPI(
    title="Application Service",
    description="API cho application",
    version="1.0.0",
    root_path="/api/application"
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

VN_TZ = timezone(timedelta(hours=7))

# ==========================
# ROUTE
# ==========================

# /api/application/me/get-application
@app.get(
    "/me/get-application",
    response_model=List[ApplicationModel],
    status_code=status.HTTP_200_OK,
    tags=["Application"]
)
async def get_me_applications(
    # Header Request
    token: str = Security(oauth2_scheme),
    # Query Param
    skip: int = Query(0, ge=0, description="Bỏ qua số lượng bản ghi (dùng cho phân trang). Mặc định = 0."),
    limit: int = Query(20, ge=1, description="Số lượng bản ghi muốn lấy. Mặc định = 20."),
):
    # Xác thực user
    current_user = await get_current_user(token, users_collection)

    # Query MongoDB: chỉ lấy applications của user hiện tại
    query = {"tutor_id": ObjectId( current_user.id )}

    # Lấy dữ liệu + phân trang
    cursor = applications_collection.find(query).skip(skip).limit(limit)
    applications_list = list(cursor)

    if not applications_list:
        raise HTTPException(status_code=404, detail="No applications found")

    # Convert ObjectId → str và trả về ApplicationModel
    return [
        ApplicationModel(
            id=str(app["_id"]),
            post_id=str(app["post_id"]),
            tutor_id=str(app["tutor_id"]),
            application_status=app["application_status"],
            applied_at=app["applied_at"]
        )
        for app in applications_list
    ]

# /api/application/get-application-by-post
@app.post(
    "/get-application-by-post",
    response_model=List[ApplicationModel],
    status_code=status.HTTP_200_OK,
    tags=["Application"]
)
async def get_applications_of_post(
    # Header Request
    token: str = Security(oauth2_scheme),
    # Body Request
    input_data: GetApplicationModel = Body(...),
    # Query Param
    skip: int = Query(0, ge=0, description="Bỏ qua số lượng bản ghi (dùng cho phân trang). Mặc định = 0."),
    limit: int = Query(20, ge=1, description="Số lượng bản ghi muốn lấy. Mặc định = 20."),
    # Lọc theo trạng thái nếu muốn
    application_status: Optional[List[str]] = Query(
        None,
        description=(
            "Hỗ trợ nhiều giá trị: pending, accepted, rejected. "
            "Ví dụ: ?application_status=pending&application_status=accepted"
        )
    )
):
    # Xác thực user (token vẫn cần)
    current_user = await get_current_user(token, users_collection)

    # Query MongoDB: chỉ filter post_id
    query = {"post_id": ObjectId(input_data.post_id)}

    # Filter theo trạng thái nếu có
    if application_status:
        query["application_status"] = {"$in": application_status}

    # Lấy dữ liệu + phân trang
    cursor = applications_collection.find(query).skip(skip).limit(limit)
    application_list = list(cursor)

    if not application_list:
        raise HTTPException(
            status_code=404,
            detail="No applications found"
        )

    # Convert ObjectId → str cho response
    return [
        ApplicationModel(
            id=str(app["_id"]),
            post_id=str(app["post_id"]),
            tutor_id=str(app["tutor_id"]),
            application_status=app["application_status"],
            applied_at=app["applied_at"]
        )
        for app in application_list
    ]

# /api/application/add-application
@app.post(
    "/add-application",
    response_model=ApplicationModel,
    status_code=status.HTTP_201_CREATED,
    tags=["Application"]
)
async def add_application(
    # Header Request
    token: str = Security(oauth2_scheme),
    # Body Request
    input_data: AddApplicationModel = Body(...),
):
    # Xác thực user
    current_user = await get_current_user(token, users_collection)
    
    # Convert model -> dict: for python to process
    _dict_input_data = input_data.model_dump()

    _dict_input_data["tutor_id"] = current_user.id
    _dict_input_data["application_status"] = "pending"
    _dict_input_data["applied_at"] = datetime.now(VN_TZ)

    # Lưu vào DB
    inserted_id = applications_collection.insert_one({
        "post_id": ObjectId( _dict_input_data["post_id"] ),
        "tutor_id": ObjectId( _dict_input_data["tutor_id"] ),
        "application_status": _dict_input_data["application_status"],
        "applied_at": _dict_input_data["applied_at"]
    }).inserted_id

    # Lấy lại bản ghi vừa tạo
    saved = applications_collection.find_one({"_id": inserted_id})

    # Convert ObjectId → string cho response model
    saved["id"] = str(saved["_id"])
    saved["post_id"] = str(saved["post_id"])
    saved["tutor_id"] = str(saved["tutor_id"])
    saved.pop("_id")

    return ApplicationModel(**saved)

# /api/application/delete-application
@app.post(
    "/delete-application",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    tags=["Application"]
)
async def delete_application(
    token: str = Security(oauth2_scheme),
    input_data: DeleteApplicationModel = Body(...)
):
    # Xác thực user
    current_user = await get_current_user(token, users_collection)
    tutor_id = str(current_user.id)

    app_id = input_data.id

    application = applications_collection.find_one({"_id": ObjectId(app_id)})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Kiểm tra quyền: chỉ tutor tạo application mới được xóa
    if str(application["tutor_id"]) != tutor_id:
        raise HTTPException(status_code=403, detail="Not allowed to delete this application")

    # Xóa application
    result = applications_collection.delete_one({"_id": ObjectId(app_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Failed to delete application")

    return {"status": "success", "message": "Application deleted successfully"}

# /api/application/update-status
@app.post(
    "/update-status",
    response_model=ApplicationModel,
    status_code=status.HTTP_200_OK,
    tags=["Application"]
)
async def update_application_status(
    token: str = Security(oauth2_scheme),
    input_data: UpdateApplicationModel = Body(...),  # model chứa app_id + application_status
):
    # Xác thực user
    current_user = await get_current_user(token, users_collection)
    user_id = str(current_user.id)

    app_id = input_data.id

    # Lấy application từ DB
    application = applications_collection.find_one({"_id": ObjectId(app_id)})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Lấy post liên quan
    post = posts_collection.find_one({"_id": ObjectId(application["post_id"])})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Chỉ owner của post mới được update, nhưng admin cũng được phép
    try:
        db_user = users_collection.find_one({"_id": ObjectId(user_id)})
    except Exception:
        db_user = None

    is_admin = False
    if db_user:
        is_admin = db_user.get("role") == "admin"

    if str(post["creator_id"]) != user_id and not is_admin:
        raise HTTPException(status_code=403, detail="Not allowed to update this application")

    # Nếu input_data.application_status là None hoặc "" thì mặc định thành "rejected"
    new_status = input_data.application_status
    if not new_status or new_status.strip() == "":
        new_status = "rejected"

    # Cập nhật trạng thái application
    applications_collection.update_one(
        {"_id": ObjectId(app_id)},
        {"$set": {"application_status": new_status, "updated_at": datetime.now(VN_TZ)}}
    )

    # Lấy lại application sau khi cập nhật
    updated_app = applications_collection.find_one({"_id": ObjectId(app_id)})

    # Convert ObjectId → str
    updated_app["id"] = str(updated_app["_id"])
    updated_app["post_id"] = str(updated_app["post_id"])
    updated_app["tutor_id"] = str(updated_app["tutor_id"])
    updated_app.pop("_id", None)

    # If admin accepted the application, notify the tutor by email
    try:
        if new_status == "accepted":
            tutor = users_collection.find_one({"_id": ObjectId(updated_app["tutor_id"])})
            post = posts_collection.find_one({"_id": ObjectId(updated_app["post_id"])})
            tutor_email = tutor.get("email") if tutor else None
            post_title = post.get("title") if post else ""

            if tutor_email:
                # Call email service to notify tutor (using booking email template)
                try:
                    parent = users_collection.find_one({"_id": ObjectId(user_id)})
                    parent_name = parent.get("display_name") if parent else ""
                    resp = requests.post(
                        f"{EMAIL_SERVICE_URL}/send-email",
                        json={
                            "applicant_email": tutor_email,
                            "applicant_name": tutor.get("display_name"),
                            "parent_name": parent_name,
                            "post_title": post_title,
                            "poster_email": parent.get("email") if parent else "",
                            "poster_phone": parent.get("phone") if parent else "",
                            "content": "Your application has been approved.",
                        },
                        timeout=5,
                    )
                    if resp.status_code != 200:
                        print("Email service returned non-200 when notifying tutor:", resp.status_code, resp.text)
                except Exception as e:
                    # swallow email errors but log to stdout
                    print("Failed to send tutor notification email", str(e))
    except Exception:
        pass
    return ApplicationModel(**updated_app)


# /api/application/health
@app.get(
    "/health",
    tags=["System"],
    status_code=200
)
async def health_check():
    return {"status": "ok"}