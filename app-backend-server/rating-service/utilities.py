from types import SimpleNamespace


def hash_password(plain_password: str) -> str:
    import bcrypt
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    import bcrypt
    return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))


def get_user_from_db(username: str, users_collection):
    """Return a lightweight user-like object (SimpleNamespace) or None.

    Other services return a Pydantic UserModel, but rating-service doesn't
    define that model. Returning a SimpleNamespace provides the `.id`
    attribute that `jwt_utils.get_current_user` and other code expect.
    """
    user = users_collection.find_one({"username": username})
    if not user:
        return None

    return SimpleNamespace(
        id=str(user.get("_id")),
        username=user.get("username"),
        email=user.get("email"),
        phone=user.get("phone"),
        password_hash=user.get("password_hash"),
        display_name=user.get("display_name"),
        subjects=user.get("subjects", []),
        levels=user.get("levels", []),
        gender=user.get("gender"),
        address=user.get("address"),
        bio=user.get("bio")
    )
