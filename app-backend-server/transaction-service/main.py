from typing import List, Optional, Literal
from fastapi import FastAPI, HTTPException, Security, status, Query, Body, status
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId
from datetime import datetime, timezone, timedelta

from shared.database import users_collection, posts_collection, transactions_collection, applications_collection
from models import TransactionModel, AddTransactionModel, AddApplicationPaymentModel
import requests
from shared.config import EMAIL_SERVICE_URL
from jwt_utils import get_current_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

VN_TZ = timezone(timedelta(hours=7))
UTC_TZ = timezone.utc

# ==========================
# FASTAPI APP
# ==========================
app = FastAPI(
    title="Transaction Service",
    description="API cho transaction",
    version="1.0.0",
    root_path="/api/transaction"
)

# ==========================
# ROUTE
# ==========================

# /api/transaction/me/get-transaction
@app.get(
    "/me/get-transaction",
    status_code=status.HTTP_200_OK,
    response_model=List[TransactionModel],
    tags=["Transaction"]
)
async def get_transactions(
    token: str = Security(oauth2_scheme),
    skip: int = Query(0, ge=0, description="Số bản ghi bỏ qua"),
    limit: int = Query(10, ge=1, description="Số bản ghi trả về"),
    transaction_status: Optional[str] = Query(None, description="Trạng thái giao dịch, bỏ trống để lấy tất cả")
):
    current_user = await get_current_user(token, users_collection)
    user_id = str(current_user.id)

    # Build query
    query = {"payer_id": ObjectId(user_id)}
    if transaction_status:
        query["transaction_status"] = transaction_status

    # Lấy dữ liệu
    cursor = transactions_collection.find(query).skip(skip).limit(limit)
    transaction_list = list(cursor)

    if not transaction_list:
        raise HTTPException(status_code=404, detail="No transactions found")

    results = []
    for t in transaction_list:
        created = t.get("created_at")
        if isinstance(created, datetime):
            if created.tzinfo is None:
                created = created.replace(tzinfo=UTC_TZ)
            # Convert to VN timezone for client display
            created_vn = created.astimezone(VN_TZ)
        else:
            created_vn = None

        results.append(TransactionModel(
            id=str(t["_id"]),
            post_id=str(t["post_id"]),
            payer_id=str(t["payer_id"]),
            amount_money=t["amount_money"],
            transaction_status=t.get("transaction_status"),
            created_at=created_vn
        ))

    return results

# /api/transaction/add-transaction
@app.post(
    "/add-transaction",
    status_code=status.HTTP_201_CREATED,
    response_model=TransactionModel,
    tags=["Transaction"]
)
async def add_transaction(
    token: str = Security(oauth2_scheme),
    input_data: AddTransactionModel = Body(...)
):
    current_user = await get_current_user(token, users_collection)
    user_id = str(current_user.id)

    # Validate post_id
    post = posts_collection.find_one({"_id": ObjectId(input_data.post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Người đăng bài
    creator_id = str(post.get("creator_id"))

    # Chỉ người đăng bài mới có quyền thanh toán
    if user_id != creator_id:
        raise HTTPException(
            status_code=403,
            detail="Only the creator of this post can create a transaction"
        )
    
    # Không cho thanh toán nhiều lần
    if post.get("post_status") == "active":
        raise HTTPException(
            status_code=400,
            detail="This post is already active"
        )

    # ---- CHECK BALANCE ----
    user_data = users_collection.find_one({"_id": ObjectId(user_id)})

    # nếu không có balance thì mặc định 0
    balance = user_data.get("balance", 0)

    if balance < input_data.amount_money:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient balance. Your balance: {balance}, required: {input_data.amount_money}"
        )

    # Trừ tiền user
    new_balance = balance - input_data.amount_money

    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"balance": new_balance}}
    )

    new_transaction = {
        "post_id": ObjectId(input_data.post_id),
        "payer_id": ObjectId(user_id),
        "amount_money": input_data.amount_money,
        "transaction_status": "paid",
        # Store timestamp in UTC (naive) so DB uses a consistent baseline
        "created_at": datetime.utcnow()
    }

    result = transactions_collection.insert_one(new_transaction)

    # Update post_status sau khi thanh toán
    posts_collection.update_one(
        {"_id": ObjectId(input_data.post_id)},
        {"$set": {"post_status": "inactive"}}
    )

    # ---- RESPONSE ----
    return TransactionModel(
        id=str(result.inserted_id),
        post_id=str(input_data.post_id),
        payer_id=str(user_id),
        amount_money=input_data.amount_money,
        transaction_status="paid",
        created_at=new_transaction["created_at"]
    )


@app.post(
    "/pay-application",
    status_code=status.HTTP_201_CREATED,
    response_model=TransactionModel,
    tags=["Transaction"]
)
async def pay_application(
    token: str = Security(oauth2_scheme),
    input_data: AddApplicationPaymentModel = Body(...)
):
    current_user = await get_current_user(token, users_collection)
    tutor_id = str(current_user.id)

    # Find application
    application = applications_collection.find_one({"_id": ObjectId(input_data.application_id)})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Only the tutor who created the application can pay
    if str(application.get("tutor_id")) != tutor_id:
        raise HTTPException(status_code=403, detail="Not allowed to pay for this application")

    post_id = str(application.get("post_id"))
    post = posts_collection.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # ---- CHECK BALANCE ----
    user_data = users_collection.find_one({"_id": ObjectId(tutor_id)})
    balance = user_data.get("balance", 0)
    if balance < input_data.amount_money:
        raise HTTPException(status_code=400, detail=f"Insufficient balance. Your balance: {balance}, required: {input_data.amount_money}")

    # Deduct balance
    users_collection.update_one({"_id": ObjectId(tutor_id)}, {"$set": {"balance": balance - input_data.amount_money}})

    # Create transaction
    new_transaction = {
        "post_id": ObjectId(post_id),
        "payer_id": ObjectId(tutor_id),
        "amount_money": input_data.amount_money,
        "transaction_status": "paid",
        "created_at": datetime.utcnow()
    }
    tx_result = transactions_collection.insert_one(new_transaction)

    # Update application status to accepted_and_paid
    applications_collection.update_one({"_id": ObjectId(input_data.application_id)}, {"$set": {"application_status": "accepted_and_paid", "updated_at": datetime.now(VN_TZ)}})

    # Assign tutor to post
    posts_collection.update_one({"_id": ObjectId(post_id)}, {"$set": {"assigned_tutor": ObjectId(tutor_id), "post_status": "active"}})

    # Notify parent via email-service
    try:
        parent = users_collection.find_one({"_id": ObjectId(str(post.get("creator_id")))})
        parent_email = parent.get("email") if parent else None
        if parent_email:
            try:
                resp = requests.post(f"{EMAIL_SERVICE_URL}/send-parent-notify", json={
                    "parent_email": parent_email,
                    "parent_name": parent.get("display_name"),
                    "post_title": post.get("title"),
                }, timeout=5)
                if resp.status_code != 200:
                    print("Email service returned non-200 when notifying parent:", resp.status_code, resp.text)
            except Exception as e:
                print("Failed to send parent notification email", str(e))
    except Exception:
        print("Failed to send parent notification email")

    return TransactionModel(
        id=str(tx_result.inserted_id),
        post_id=post_id,
        payer_id=tutor_id,
        amount_money=input_data.amount_money,
        transaction_status="paid",
        created_at=new_transaction["created_at"]
    )

# /api/transaction/health
@app.get(
    "/health",
    tags=["System"],
    status_code=200
)
async def health_check():
    return {"status": "ok"}