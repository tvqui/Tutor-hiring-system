from fastapi import FastAPI, HTTPException, Depends, Form, Request, Security, status, Header, Body
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId
from typing import List

from models import TokenModel, UserModel, LoginModel, CertificateModel, UpdateProfileModel, AddCertificateModel, DelCertificateModel, GetProfileByUserIDModel, GetCertificateByUserIDModel, ProfileModel, ProofImageModel, AddProofImageModel, DelProofImageModel
from shared.database import users_collection, certificates_collection, ratings_collection, proof_images_collection
from datetime import datetime
from utilities import verify_password, get_user_from_db
from init_db import init_db
from jwt_utils import create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from models import UpdateProfileStatusModel, UpdateCertificateStatusModel

# INIT DB
init_db()

# ==========================
# FASTAPI APP
# ==========================
app = FastAPI(
    title="Auth Service",
    description="API cho authentication, JWT token, certificates",
    version="1.0.0",
    root_path="/api/auth"
)

# ==========================
# OAUTH2 (hiển thị nút Authorize)
# ==========================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ==========================
# LOGIN DATA (Form hoặc JSON)
# ==========================
async def get_login_data(request: Request):
    try:
        data = await request.json()
        return LoginModel(**data)
    except:
        form = await request.form()
        return LoginModel(
            username=form.get("username"),
            password=form.get("password")
        )

# ==========================
# ROUTES
# ==========================

# /api/auth/login
@app.post(
    "/login",
    response_model=TokenModel,
    tags=["Authentication"],
    status_code=status.HTTP_200_OK
)
async def login(data: LoginModel = Depends(get_login_data)):
    user = get_user_from_db(data.username, users_collection)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Sai username hoặc password")

    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# /api/auth/me/get-profile
@app.get(
    "/me/get-profile",
    response_model=UserModel,
    tags=["Profile"],
    status_code=status.HTTP_200_OK
)
async def me(token: str = Security(oauth2_scheme)):
    current_user = await get_current_user(
        token=token,
        users_collection=users_collection
    )

    # Fetch fresh user doc to attach rating stats
    user = users_collection.find_one({"_id": ObjectId(current_user.id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = str(user.get("_id"))

    # compute rating stats
    stats = list(ratings_collection.aggregate([
        {"$match": {"tutor_id": ObjectId(user_id)}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}}
    ]))

    if stats:
        user["avg_rating"] = round(float(stats[0].get("avg", 0.0)), 2)
        user["rating_count"] = int(stats[0].get("count", 0))
    else:
        user["avg_rating"] = None
        user["rating_count"] = 0

    user["id"] = str(user["_id"])
    user.pop("_id", None)
    return UserModel(**user)

# /api/auth/get-profile-by-user-id
@app.post(
    "/get-profile-by-user-id",
    status_code=status.HTTP_200_OK,
    response_model=ProfileModel,
    tags=["Profile"]
)
async def get_profile_by_user_id(
    token: str = Security(oauth2_scheme),
    input_data: GetProfileByUserIDModel = Body(...)
):

    # Chỉ check token
    _ = await get_current_user(token, users_collection)

    # Lấy user ID từ input
    target_user_id = str(input_data.user_id)

    # Tìm user trong DB
    user = users_collection.find_one({"_id": ObjectId(target_user_id)})

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    # Chuẩn hóa dữ liệu
    user["id"] = str(user["_id"])

    # Xóa field nhạy cảm nếu tồn tại
    user.pop("password_hash", None)
    user.pop("username", None)

    # compute rating stats for the requested user
    stats = list(ratings_collection.aggregate([
        {"$match": {"tutor_id": ObjectId(target_user_id)}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}}
    ]))

    if stats:
        user["avg_rating"] = round(float(stats[0].get("avg", 0.0)), 2)
        user["rating_count"] = int(stats[0].get("count", 0))
    else:
        user["avg_rating"] = None
        user["rating_count"] = 0

    # Trả về ProfileModel (tự động chỉ lấy field hợp lệ)
    return ProfileModel(**user)


# Admin: update profile status (unverified|pending|rejected|accepted)
@app.post(
    "/admin/update-profile-status",
    status_code=status.HTTP_200_OK,
    tags=["Admin"]
)
async def admin_update_profile_status(
    token: str = Security(oauth2_scheme),
    input_data: UpdateProfileStatusModel = Body(...)
):
    current_user = await get_current_user(token, users_collection)
    if not getattr(current_user, 'role', None) == 'admin':
        raise HTTPException(status_code=403, detail="Admin privileges required")

    target_id = input_data.user_id
    try:
        users_collection.update_one({"_id": ObjectId(target_id)}, {"$set": {"status": input_data.status}})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user id")

    user = users_collection.find_one({"_id": ObjectId(target_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user["id"] = str(user["_id"]) if user.get("_id") else target_id
    user.pop("_id", None)
    return ProfileModel(**user)


# Admin: update certificate status (unverified|pending|rejected|accepted)
@app.post(
    "/admin/update-certificate-status",
    status_code=status.HTTP_200_OK,
    tags=["Admin"]
)
async def admin_update_certificate_status(
    token: str = Security(oauth2_scheme),
    input_data: UpdateCertificateStatusModel = Body(...)
):
    current_user = await get_current_user(token, users_collection)
    if not getattr(current_user, 'role', None) == 'admin':
        raise HTTPException(status_code=403, detail="Admin privileges required")

    cert_id = input_data.certificate_id
    try:
        certificates_collection.update_one({"_id": ObjectId(cert_id)}, {"$set": {"status": input_data.status}})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid certificate id")

    cert = certificates_collection.find_one({"_id": ObjectId(cert_id)})
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    cert["id"] = str(cert["_id"]) if cert.get("_id") else cert_id
    cert["user_id"] = str(cert["user_id"]) if cert.get("user_id") else None
    return CertificateModel(**cert)

# /api/auth/me/get-certificate
@app.get(
    "/me/get-certificate",
    response_model=List[CertificateModel],
    tags=["Certificate"],
    status_code=status.HTTP_200_OK
)
async def get_certificate(token: str = Security(oauth2_scheme)):
    current_user = await get_current_user(
        token=token,
        users_collection=users_collection
    )

    certificates = list(certificates_collection.find({"user_id": ObjectId(current_user.id)}))

    if not certificates:
        raise HTTPException(status_code=404, detail="Không tìm thấy chứng chỉ")

    return [
        CertificateModel(
            id=str(c.get("_id")),
            user_id=str(c.get("user_id")),
            certificate_type=c.get("certificate_type"),
            description=c.get("description"),
            url=c.get("url"),
            filename=c.get("filename"),
            uploaded_at=c.get("uploaded_at"),
            status=c.get("status")
        )
        for c in certificates
    ]


# api/auth/me/add-proof-image
@app.post(
    "/me/add-proof-image",
    response_model=ProofImageModel,
    status_code=status.HTTP_201_CREATED,
    tags=["Profile", "Certificate"]
)
async def add_proof_image(
    token: str = Security(oauth2_scheme),
    input_data: AddProofImageModel = Body(...)
):
    current_user = await get_current_user(token, users_collection)

    # validate type
    if input_data.type not in ["profile", "certificate"]:
        raise HTTPException(status_code=400, detail="Invalid type; must be 'profile' or 'certificate'")

    # validate type_id
    try:
        type_obj_id = ObjectId(input_data.type_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid type_id")

    doc = {
        "type": input_data.type,
        "type_id": type_obj_id,
        "image": input_data.image,
        "created_at": datetime.utcnow(),
        "user_id": ObjectId(current_user.id)
    }

    res = proof_images_collection.insert_one(doc)
    new = proof_images_collection.find_one({"_id": res.inserted_id})
    new["id"] = str(new["_id"])
    new["type_id"] = str(new["type_id"]) if new.get("type_id") else None
    new["user_id"] = str(new.get("user_id")) if new.get("user_id") else None

    return ProofImageModel(**new)


# api/auth/me/delete-proof-image
@app.post(
    "/me/delete-proof-image",
    status_code=status.HTTP_200_OK,
    tags=["Profile", "Certificate"]
)
async def delete_proof_image(
    token: str = Security(oauth2_scheme),
    input_data: DelProofImageModel = Body(...)
):
    current_user = await get_current_user(token, users_collection)

    try:
        img = proof_images_collection.find_one({"_id": ObjectId(input_data.id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")

    if not img:
        raise HTTPException(status_code=404, detail="Proof image not found")

    # allow delete if owner or admin
    owner_id = str(img.get("user_id")) if img.get("user_id") else None
    if owner_id != current_user.id and getattr(current_user, 'role', None) != 'admin':
        raise HTTPException(status_code=403, detail="Not allowed to delete this proof image")

    proof_images_collection.delete_one({"_id": ObjectId(input_data.id)})
    return {"detail": "deleted"}


# User: request profile verification (sets own profile status to 'pending')
@app.post(
    "/me/request-profile-verification",
    status_code=status.HTTP_200_OK,
    tags=["Profile"]
)
async def request_profile_verification(
    token: str = Security(oauth2_scheme)
):
    current_user = await get_current_user(token, users_collection)
    user_id = current_user.id
    users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"status": "pending"}})
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    user["id"] = str(user.get("_id"))
    user.pop("_id", None)
    return ProfileModel(**user)


# User: request certificate verification (sets certificate status to 'pending')
@app.post(
    "/me/request-certificate-verification",
    status_code=status.HTTP_200_OK,
    tags=["Certificate"]
)
async def request_certificate_verification(
    token: str = Security(oauth2_scheme),
    input_data: dict = Body(...)
):
    current_user = await get_current_user(token, users_collection)
    cert_id = input_data.get("certificate_id")
    if not cert_id:
        raise HTTPException(status_code=400, detail="certificate_id is required")
    try:
        oid = ObjectId(cert_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid certificate_id")

    # ensure certificate belongs to current user
    cert = certificates_collection.find_one({"_id": oid, "user_id": ObjectId(current_user.id)})
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found or not owned by user")

    certificates_collection.update_one({"_id": oid}, {"$set": {"status": "pending"}})
    cert = certificates_collection.find_one({"_id": oid})
    cert["id"] = str(cert.get("_id"))
    cert["user_id"] = str(cert.get("user_id"))
    return CertificateModel(**cert)


# api/auth/get-proof-images-by-type
@app.post(
    "/get-proof-images-by-type",
    response_model=List[ProofImageModel],
    status_code=status.HTTP_200_OK,
    tags=["Profile", "Certificate"]
)
async def get_proof_images_by_type(
    token: str = Security(oauth2_scheme),
    input_data: dict = Body(...)
):
    """Request body: { "type": "profile"|"certificate", "type_id": "<id>" }
    Returns list of proof images for that type/type_id.
    """
    # validate token
    _ = await get_current_user(token, users_collection)

    t = input_data.get("type")
    type_id = input_data.get("type_id")
    if t not in ["profile", "certificate"]:
        raise HTTPException(status_code=400, detail="Invalid type")
    try:
        oid = ObjectId(type_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid type_id")

    imgs = list(proof_images_collection.find({"type": t, "type_id": oid}))
    result = []
    for im in imgs:
        im["id"] = str(im.get("_id"))
        im["type_id"] = str(im.get("type_id")) if im.get("type_id") else None
        im["user_id"] = str(im.get("user_id")) if im.get("user_id") else None
        result.append(ProofImageModel(**im))

    return result

# /api/auth/get-certificate-by-user-id
@app.post(
    "/get-certificate-by-user-id",
    response_model=List[CertificateModel],
    tags=["Certificate"],
    status_code=status.HTTP_200_OK
)
async def get_certificate_by_user_id(
    token: str = Security(oauth2_scheme),
    input_data: GetCertificateByUserIDModel = Body(...)
):
    # Verify token is valid
    _ = await get_current_user(token, users_collection)

    target_user_id = str(input_data.user_id)

    # Lấy danh sách chứng chỉ của user khác
    certificates = list(certificates_collection.find({
        "user_id": ObjectId(target_user_id)
    }))

    # Return empty list if no certificates found (not an error)
    if not certificates:
        return []

    return [
        CertificateModel(
            id=str(c.get("_id")),
            user_id=str(c.get("user_id")),
            certificate_type=c.get("certificate_type"),
            description=c.get("description"),
            url=c.get("url"),
            filename=c.get("filename"),
            uploaded_at=c.get("uploaded_at"),
            status=c.get("status")
        )
        for c in certificates
    ]


# Admin: get profiles by status
@app.post(
    "/get-profiles-by-status",
    response_model=List[ProfileModel],
    status_code=status.HTTP_200_OK,
    tags=["Admin"]
)
async def get_profiles_by_status(
    token: str = Security(oauth2_scheme),
    input_data: dict = Body(...)
):
    """Request body: { "status": "unverified|pending|rejected|accepted", "skip": 0, "limit": 50 }
    Returns list of ProfileModel for users matching status. Admin only.
    """
    current_user = await get_current_user(token, users_collection)
    if getattr(current_user, 'role', None) != 'admin':
        raise HTTPException(status_code=403, detail="Admin privileges required")

    status_filter = input_data.get('status')
    if not status_filter:
        raise HTTPException(status_code=400, detail="status is required")

    try:
        skip = int(input_data.get('skip', 0))
        limit = int(input_data.get('limit', 50))
    except Exception:
        raise HTTPException(status_code=400, detail="skip and limit must be integers")

    users = list(users_collection.find({"status": status_filter}).skip(skip).limit(limit))
    result = []
    for u in users:
        # compute rating stats
        uid = str(u.get("_id"))
        stats = list(ratings_collection.aggregate([
            {"$match": {"tutor_id": ObjectId(uid)}},
            {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}}
        ]))

        if stats:
            u["avg_rating"] = round(float(stats[0].get("avg", 0.0)), 2)
            u["rating_count"] = int(stats[0].get("count", 0))
        else:
            u["avg_rating"] = None
            u["rating_count"] = 0

        u["id"] = str(u.get("_id"))
        # remove sensitive
        u.pop("password_hash", None)
        u.pop("username", None)
        u.pop("_id", None)
        result.append(ProfileModel(**u))

    return result


# Admin: get certificates by status
@app.post(
    "/get-certificates-by-status",
    response_model=List[CertificateModel],
    status_code=status.HTTP_200_OK,
    tags=["Admin"]
)
async def get_certificates_by_status(
    token: str = Security(oauth2_scheme),
    input_data: dict = Body(...)
):
    """Request body: { "status": "unverified|pending|rejected|accepted", "skip": 0, "limit": 50 }
    Returns list of CertificateModel filtered by status. Admin only.
    """
    current_user = await get_current_user(token, users_collection)
    if getattr(current_user, 'role', None) != 'admin':
        raise HTTPException(status_code=403, detail="Admin privileges required")

    status_filter = input_data.get('status')
    if not status_filter:
        raise HTTPException(status_code=400, detail="status is required")

    try:
        skip = int(input_data.get('skip', 0))
        limit = int(input_data.get('limit', 50))
    except Exception:
        raise HTTPException(status_code=400, detail="skip and limit must be integers")

    certs = list(certificates_collection.find({"status": status_filter}).skip(skip).limit(limit))
    out = []
    for c in certs:
        c["id"] = str(c.get("_id"))
        c["user_id"] = str(c.get("user_id")) if c.get("user_id") else None
        out.append(CertificateModel(**{
            "id": c["id"],
            "certificate_type": c.get("certificate_type"),
            "description": c.get("description"),
            "url": c.get("url"),
            "filename": c.get("filename"),
            "uploaded_at": c.get("uploaded_at"),
            "status": c.get("status")
        }))

    return out

# api/auth/me/update-profile
@app.post(
    "/me/update-profile",
    response_model=UserModel,
    status_code=status.HTTP_200_OK,
    tags=["Profile"]
)
async def update_profile(
    token: str = Security(oauth2_scheme),
    input_data: UpdateProfileModel = Body(...)
):
    current_user = await get_current_user(token, users_collection)
    user_id = current_user.id

    # Giữ lại field có giá trị thực sự
    update_data = {
        key: value for key, value in input_data.dict().items()
        if value not in [None, ""]
    }

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No valid fields to update."
        )

    result = users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    # Lấy user mới nhất sau khi update
    user = users_collection.find_one({"_id": ObjectId(user_id)})

    # Convert MongoDB object → UserModel
    # attach rating stats
    stats = list(ratings_collection.aggregate([
        {"$match": {"tutor_id": ObjectId(user_id)}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}}
    ]))

    if stats:
        user["avg_rating"] = round(float(stats[0].get("avg", 0.0)), 2)
        user["rating_count"] = int(stats[0].get("count", 0))
    else:
        user["avg_rating"] = None
        user["rating_count"] = 0

    user["id"] = str(user["_id"])
    user.pop("_id", None)

    return UserModel(**user)

# api/auth/me/update-certificate
@app.post(
    "/me/update-certificate",
    response_model=CertificateModel,
    status_code=status.HTTP_200_OK,
    tags=["Certificate"]
)
async def update_certificate(
    token: str = Security(oauth2_scheme),
    input_data: CertificateModel = Body(...)
):
    # Lấy user từ token
    current_user = await get_current_user(token, users_collection)
    user_id = current_user.id

    if not input_data.id:
        raise HTTPException(status_code=400, detail="Certificate ID is required")

    cert_id = input_data.id

    # Chỉ giữ field có giá trị thực sự (không None, không empty string)
    update_data = {
        key: value for key, value in input_data.dict().items()
        if key != "id" and value not in [None, ""]
    }

    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update.")

    result = certificates_collection.update_one(
        {"_id": ObjectId(cert_id), "user_id": ObjectId(user_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Certificate not found or not owned by user.")

    # Lấy lại certificate sau update
    certificate = certificates_collection.find_one({"_id": ObjectId(cert_id)})

    certificate["id"] = str(certificate["_id"])
    certificate["user_id"] = str(certificate["user_id"])

    return CertificateModel(**certificate)

# api/auth/me/add-certificate
@app.post(
    "/me/add-certificate",
    response_model=CertificateModel,
    status_code=status.HTTP_201_CREATED,
    tags=["Certificate"]
)
async def add_certificate(
    token: str = Security(oauth2_scheme),
    input_data: AddCertificateModel = Body(...)
):
    # Lấy user từ token
    current_user = await get_current_user(token, users_collection)
    user_id = current_user.id

    # Tạo document mới
    cert_data = input_data.dict(exclude={"id", "user_id"})  # loại bỏ id và user_id nếu có
    cert_data["user_id"] = ObjectId(user_id)

    result = certificates_collection.insert_one(cert_data)

    # Lấy certificate vừa insert
    certificate = certificates_collection.find_one({"_id": result.inserted_id})

    certificate["id"] = str(certificate["_id"])
    certificate["user_id"] = str(certificate["user_id"])

    return CertificateModel(**certificate)

# api/auth/me/delete-certificate
@app.post(
    "/me/delete-certificate",
    status_code=status.HTTP_200_OK,
    tags=["Certificate"]
)
async def delete_certificate(
    input_data: DelCertificateModel = Body(...),
    token: str = Security(oauth2_scheme)
):
    # Lấy user từ token
    current_user = await get_current_user(token, users_collection)
    user_id = current_user.id

    certificate_id = str( input_data.id )

    # Kiểm tra certificate có tồn tại và thuộc về user không
    cert = certificates_collection.find_one({
        "_id": ObjectId(certificate_id),
        "user_id": ObjectId(user_id)
    })

    if not cert:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found or not owned by user."
        )

    # Xóa certificate
    certificates_collection.delete_one({"_id": ObjectId(certificate_id)})

    return {"detail": "Certificate deleted successfully"}

# /api/auth/health
@app.get(
    "/health",
    tags=["System"],
    status_code=status.HTTP_200_OK
)
async def health_check():
    return {"status": "ok"}
