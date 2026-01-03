# shared/database.py
from pymongo import MongoClient
import os

# ============================================
# Load ENV
# ============================================
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "27017")
DB_NAME = os.getenv("MONGO_INITDB_DATABASE", "tutor_db")

# ============================================
# Create ONE MongoClient for entire project
# ============================================
MONGO_URI = f"mongodb://{DB_HOST}:{DB_PORT}/"
client = MongoClient(MONGO_URI)

# Global database instance
db = client[DB_NAME]

# ============================================
# Export collections to be reused anywhere
# ============================================
users_collection = db.users
certificates_collection = db.certificates
posts_collection = db.posts
applications_collection = db.applications
bookings_collection = db.bookings
transactions_collection = db.transactions
ratings_collection = db.ratings
proof_images_collection = db.proof_images