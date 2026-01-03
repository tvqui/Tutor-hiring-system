from typing import List, Optional, Literal
from fastapi import FastAPI, HTTPException, Security, status, Query, Body
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime

from shared.database import posts_collection, users_collection
from models import PostModel, AddPostModel, DelPostModel
from jwt_utils import get_current_user

app = FastAPI(
    title="Post Service",
    description="API cho quản lý posts",
    version="1.0.0",
    root_path="/api/post"
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class UpdatePostStatusModel(BaseModel):
    id: str
    post_status: Literal["active", "inactive"]

@app.get(
    "/get-post",
    response_model=List[PostModel],
    status_code=status.HTTP_200_OK,
    tags=["Post"]
)
async def get_posts(
    token: str = Security(oauth2_scheme),
    scope: str = Query("me", regex="^(me|all)$", description="me: bài của user, all: bài active của tất cả"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    subject: Optional[List[str]] = Query(None),
    level: Optional[List[str]] = Query(None),
    mode: Optional[List[str]] = Query(None),
):
    query = {}

    # -------------------------
    # 1. Xử lý scope
    # -------------------------
    if scope == "me":
        # Lấy cả active + inactive của user
        current_user = await get_current_user(token, users_collection)
        query["creator_id"] = ObjectId(current_user.id)

    elif scope == "all":
        # Chỉ lấy bài inactive (bài chưa được thanh toán/kích hoạt)
        query["post_status"] = "inactive"


    # Case-insensitive regex search for each filter
    if subject:
        query["subject"] = {"$regex": subject[0], "$options": "i"} if len(subject) == 1 else {"$in": subject}
    if level:
        query["level"] = {"$regex": level[0], "$options": "i"} if len(level) == 1 else {"$in": level}
    if mode:
        query["mode"] = {"$regex": mode[0], "$options": "i"} if len(mode) == 1 else {"$in": mode}

    # Address filter (add if needed)
    address = None
    try:
        from fastapi import Request
        address = Request.query_params.get("address")
    except Exception:
        pass
    if address:
        query["address"] = {"$regex": address, "$options": "i"}

    posts_cursor = posts_collection.find(query).skip(skip).limit(limit)
    posts = list(posts_cursor)

    if not posts:
        raise HTTPException(status_code=404, detail="No posts found")

    result = []
    for p in posts:
        p["id"] = str(p["_id"])
        p["creator_id"] = str(p["creator_id"])
        result.append(PostModel(**p))

    return result

@app.post(
    "/add-post",
    response_model=PostModel,
    status_code=status.HTTP_201_CREATED,
    tags=["Post"]
)
async def add_post(
    token: str = Security(oauth2_scheme),
    input_data: AddPostModel = Body(...)
):
    current_user = await get_current_user(token, users_collection)
    
    new_post = input_data.dict()
    new_post["creator_id"] = ObjectId(current_user.id)
    new_post["created_at"] = datetime.utcnow()

    result = posts_collection.insert_one(new_post)

    # convert output
    new_post["id"] = str(result.inserted_id)
    new_post["creator_id"] = str(new_post["creator_id"])

    return PostModel(**new_post)


@app.post(
    "/delete-post",
    tags=["Post"],
    status_code=status.HTTP_200_OK
)
async def delete_post(
    input_data: DelPostModel = Body(...),
    token: str = Security(oauth2_scheme)
):
    current_user = await get_current_user(token, users_collection)

    post = posts_collection.find_one({"_id": ObjectId(input_data.id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Chỉ creator mới được phép xóa
    if str(post["creator_id"]) != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to delete this post"
        )

    posts_collection.delete_one({"_id": ObjectId(input_data.id)})

    return {"message": "Post deleted successfully"}

@app.post(
    "/update-status",
    tags=["Post"],
    status_code=status.HTTP_200_OK
)
async def update_post_status(
    input_data: UpdatePostStatusModel = Body(...),
    token: str = Security(oauth2_scheme)
):
    """
    Update post status (active/inactive)
    Only post creator can update
    """
    current_user = await get_current_user(token, users_collection)

    post = posts_collection.find_one({"_id": ObjectId(input_data.id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Chỉ creator mới được phép update, nhưng admin cũng được phép
    try:
        db_user = users_collection.find_one({"_id": ObjectId(current_user.id)})
    except Exception:
        db_user = None

    is_admin = False
    if db_user:
        is_admin = db_user.get("role") == "admin"

    if str(post["creator_id"]) != current_user.id and not is_admin:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to update this post"
        )

    posts_collection.update_one(
        {"_id": ObjectId(input_data.id)},
        {"$set": {"post_status": input_data.post_status}}
    )

    return {"message": f"Post status updated to {input_data.post_status}"}

@app.get(
    "/{post_id}",
    response_model=PostModel,
    status_code=status.HTTP_200_OK,
    tags=["Post"],
    description="Lấy chi tiết thông tin một bài post"
)
async def get_post_detail(
    post_id: str,
    token: str = Security(oauth2_scheme)
):
    """
    Lấy chi tiết của một bài post theo ID
    
    - **post_id**: ID của bài post (MongoDB ObjectId as string)
    """
    try:
        # Validate ObjectId
        post_obj_id = ObjectId(post_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid post ID format"
        )
    
    # Get current user just to verify token is valid
    await get_current_user(token, users_collection)
    
    post = posts_collection.find_one({"_id": post_obj_id})
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    # Convert ObjectId to string
    post["id"] = str(post["_id"])
    post["creator_id"] = str(post["creator_id"])
    
    return PostModel(**post)

# /api/post/health
@app.get(
    "/health",
    tags=["System"],
    status_code=200
)
async def health_check():
    return {"status": "ok"}
