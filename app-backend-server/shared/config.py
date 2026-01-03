# shared/config.py

import os

# ===========================
# SERVICE URLS
# ===========================
EMAIL_SERVICE_URL = os.getenv("EMAIL_SERVICE_URL", "http://email-service:8086/api/email")

# ===========================
# DATABASE
# ===========================
MONGO_HOST = os.getenv("MONGO_HOST", "db")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "tutor_db")

# ===========================
# JWT / AUTH
# ===========================
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# ===========================
# EMAIL
# ===========================
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "no-reply@example.com")
EMAIL_SENDER_NAME = os.getenv("EMAIL_SENDER_NAME", "IBanking Bot")