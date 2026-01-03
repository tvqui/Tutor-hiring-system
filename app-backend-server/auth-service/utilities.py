import bcrypt
from models import UserModel

def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))

def get_user_from_db(username: str, users_collection) -> UserModel | None:
    user = users_collection.find_one({"username": username})
    if not user:
        return None

    # Trả về theo dạng object 
    return UserModel(
        id=str(user["_id"]),
        username=user["username"],
        email=user.get("email"),
        phone=user.get("phone"),
        password_hash=user.get("password_hash"),
        role=user.get("role"),
        display_name=user.get("display_name"),
        subjects=user.get("subjects", []),
        levels=user.get("levels", []),
        gender=user.get("gender"),
        address=user.get("address"),
        bio=user.get("bio")
    )