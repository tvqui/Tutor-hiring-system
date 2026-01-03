# init_db.py
from shared.database import (
    users_collection,
    certificates_collection,
    posts_collection,
    applications_collection,
    bookings_collection,
    transactions_collection,
    # ratings will be added if present
    
)
from shared.database import ratings_collection
from utilities import hash_password
from datetime import datetime, timedelta, timezone
from bson import ObjectId

# Việt Nam timezone (UTC+7)
VN_TZ = timezone(timedelta(hours=7))

def init_db():
    # ==========================
    # INIT USERS
    # ==========================
    if users_collection.count_documents({}) == 0:
        users_data = [
            {
                "username": "herta",
                "email": "tranvinhquitdtu@gmail.com",
                "phone": "0901000001",
                "password_hash": hash_password("123456"),
                "display_name": "The Herta",
                "subjects": ["Nghiên cứu AI", "Khoa học dữ liệu"],
                "levels": ["Tất cả"],
                "gender": "female",
                "address": "TP. Cần Thơ",
                "bio": "Một gia sư với khả năng giảng dạy xuất sắc.",
                "balance": 1000000.0,
                "role": "customer",
                "status": "unverified"
            },
            {
                "username": "bronya",
                "email": "tranvinhquitdtu@gmail.com",
                "phone": "0902000002",
                "password_hash": hash_password("123456"),
                "display_name": "Bronya",
                "subjects": [],
                "levels": [],
                "gender": "female",
                "address": "TP. Hồ Chí Minh",
                "bio": "Một cô gái thông minh.",
                "balance": 500000.0,
                "role": "customer",
                "status": "unverified"
            },
            {
                "username": "jingyuan",
                "email": "tranvinhquitdtu@gmail.com",
                "phone": "0903000003",
                "password_hash": hash_password("123456"),
                "display_name": "Jing Yuan",
                "subjects": ["Toán", "Vật Lý"],
                "levels": ["6","7","8","9","10","11","12"],
                "gender": "male",
                "address": "Đà Nẵng",
                "bio": "Có kinh nghiệm trong việc giảng dạy các môn tự nhiên.",
                "balance": 750000.0,
                "role": "customer",
                "status": "unverified"
            },
            {
                "username": "qui",
                "email": "tranvinhquitdtu@gmail.com",
                "phone": "0901000001",
                "password_hash": hash_password("123456"),
                "display_name": "qui",
                "subjects": ["Nghiên cứu AI", "Khoa học dữ liệu"],
                "levels": ["Tất cả"],
                "gender": "female",
                "address": "TP. Cần Thơ",
                "bio": "",
                "balance": 1000000.0,
                "role": "admin",
                "status": "verified"
            },
        ]
        insert_result = users_collection.insert_many(users_data)
        user_ids = insert_result.inserted_ids
        print("Users inserted:", user_ids)
    else:
        users = list(users_collection.find({}))
        user_ids = [u["_id"] for u in users]
        print("Users already exist.")

    # ==========================
    # INIT CERTIFICATES
    # ==========================
    if certificates_collection.count_documents({}) == 0:
        certificates_data = [
            {
                "user_id": user_ids[0],
                "certificate_type": "certificate",
                "description": "Chứng chỉ AI nâng cao",
                "url": "http://viblo.asia/p/tong-hop-visual-studio-code-extensions-Ny0VGnwYLPA",
                "filename": "cv",
                "uploaded_at": datetime.now(VN_TZ),
                "status": "unverified",
            },
            {
                "user_id": user_ids[1],
                "certificate_type": "certificate",
                "description": "Chứng chỉ AI nâng cao",
                "url": "",
                "filename": "",
                "uploaded_at": datetime.now(VN_TZ),
                "status": "unverified",
            },
            {
                "user_id": user_ids[2],
                "certificate_type": "cv",
                "description": "CV ứng tuyển gia sư môn Toán",
                "url": "http://viblo.asia/p/tong-hop-visual-studio-code-extensions-Ny0VGnwYLPA",
                "filename": "adada",
                "uploaded_at": datetime.now(VN_TZ),
                "status": "unverified",
            },
        ]
        certificates_collection.insert_many(certificates_data)
        print("Certificates inserted!")
    else:
        print("Certificates already exist.")

    # ==========================
    # INIT POSTS
    # ==========================
    if posts_collection.count_documents({}) == 0:
        if len(user_ids) < 2:
            print("Not enough users for posts. Please initialize users first.")
            return

        posts_data = [
            {
                "creator_id": user_ids[0],
                "title": "Dạy Toán nâng cao lớp 10",
                "subject": "Toán",
                "level": "10",
                "address": "TP. Hồ Chí Minh",
                "salary_amount": 200000.00,
                "sessions_per_week": 2,
                "minutes_per_session": 90,
                "preferred_times": "Chiều thứ 3 và thứ 6",
                "student_info": "Học sinh lớp 10, điểm trung bình 8.5",
                "requirements": "Có kinh nghiệm dạy học 2 năm",
                "mode": "offline",
                "post_status": "inactive",
                "created_at": datetime.now(VN_TZ),
                "updated_at": datetime.now(VN_TZ),
            },
            {
                "creator_id": user_ids[1],
                "title": "Gia sư Vật Lý lớp 9",
                "subject": "Vật Lý",
                "level": "9",
                "address": "Hà Nội",
                "salary_amount": 150000.00,
                "sessions_per_week": 3,
                "minutes_per_session": 60,
                "preferred_times": "Buổi sáng các ngày trong tuần",
                "student_info": "Học sinh lớp 9, cần chuẩn bị thi vào 10",
                "requirements": "Có kinh nghiệm dạy online",
                "mode": "online",
                "post_status": "active",
                "created_at": datetime.now(VN_TZ),
                "updated_at": datetime.now(VN_TZ),
            },
            {###################################
                "creator_id": user_ids[1],
                "title": "Gia sư Tiếng Anh giao tiếp",
                "subject": "Tiếng Anh",
                "level": "Giao tiếp",
                "address": "Hà Nội",
                "salary_amount": 180000.00,
                "sessions_per_week": 3,
                "minutes_per_session": 75,
                "preferred_times": "Tối thứ 2, 4, 6",
                "student_info": "Người đi làm, cần luyện speaking",
                "requirements": "Giáo viên có chứng chỉ IELTS 7.0+",
                "mode": "online",
                "post_status": "active",
                "created_at": datetime.now(VN_TZ),
                "updated_at": datetime.now(VN_TZ),
            },
            {
                "creator_id": user_ids[2],
                "title": "Gia sư Hóa lớp 11 chuyên đề phản ứng hữu cơ",
                "subject": "Hóa",
                "level": "11",
                "address": "TP. Hồ Chí Minh",
                "salary_amount": 220000.00,
                "sessions_per_week": 2,
                "minutes_per_session": 90,
                "preferred_times": "Chiều thứ 3 và Chủ nhật",
                "student_info": "Học sinh lớp 11, muốn thi vào lớp chuyên Hóa",
                "requirements": "Sinh viên năm 3 ngành Hóa hoặc giáo viên",
                "mode": "offline",
                "post_status": "inactive",
                "created_at": datetime.now(VN_TZ),
                "updated_at": datetime.now(VN_TZ),
            },
            {
                "creator_id": user_ids[1],
                "title": "Gia sư Lập trình Python cơ bản",
                "subject": "Tin học",
                "level": "Cơ bản",
                "address": "Online",
                "salary_amount": 250000.00,
                "sessions_per_week": 2,
                "minutes_per_session": 120,
                "preferred_times": "Tối thứ 7 và Chủ nhật",
                "student_info": "Sinh viên năm nhất, muốn học Python để làm dự án",
                "requirements": "Có kinh nghiệm giảng dạy online",
                "mode": "online",
                "post_status": "active",
                "created_at": datetime.now(VN_TZ),
                "updated_at": datetime.now(VN_TZ),
            },
            {
                "creator_id": user_ids[1],
                "title": "Gia sư Ngữ Văn lớp 8 - luyện viết nghị luận",
                "subject": "Ngữ Văn",
                "level": "8",
                "address": "Đà Nẵng",
                "salary_amount": 130000.00,
                "sessions_per_week": 2,
                "minutes_per_session": 60,
                "preferred_times": "Chiều thứ 5 và thứ 7",
                "student_info": "Học sinh lớp 8, viết văn yếu",
                "requirements": "Giáo viên có kinh nghiệm dạy THCS",
                "mode": "offline",
                "post_status": "active",
                "created_at": datetime.now(VN_TZ),
                "updated_at": datetime.now(VN_TZ),
            },
            {
                "creator_id": user_ids[2],
                "title": "Gia sư Sinh học lớp 12 luyện thi THPT QG",
                "subject": "Sinh học",
                "level": "12",
                "address": "Cần Thơ",
                "salary_amount": 240000.00,
                "sessions_per_week": 3,
                "minutes_per_session": 90,
                "preferred_times": "Tối các ngày trong tuần",
                "student_info": "Học sinh 12 muốn đạt 9+ Sinh",
                "requirements": "Có kinh nghiệm luyện thi đại học",
                "mode": "offline",
                "post_status": "inactive",
                "created_at": datetime.now(VN_TZ),
                "updated_at": datetime.now(VN_TZ),
            },
            {
                "creator_id": user_ids[1],
                "title": "Gia sư Toán lớp 6 - củng cố kiến thức nền",
                "subject": "Toán",
                "level": "6",
                "address": "Hải Phòng",
                "salary_amount": 120000.00,
                "sessions_per_week": 2,
                "minutes_per_session": 60,
                "preferred_times": "Tối thứ 3 và thứ 5",
                "student_info": "Học sinh lớp 6 chậm tiếp thu",
                "requirements": "Kiên nhẫn, biết cách giảng giải dễ hiểu",
                "mode": "offline",
                "post_status": "active",
                "created_at": datetime.now(VN_TZ),
                "updated_at": datetime.now(VN_TZ),
            },
            {
                "creator_id": user_ids[1],
                "title": "Gia sư tiếng Nhật N5",
                "subject": "Tiếng Nhật",
                "level": "N5",
                "address": "Online",
                "salary_amount": 200000.00,
                "sessions_per_week": 3,
                "minutes_per_session": 60,
                "preferred_times": "Tối thứ 2, 4, 6",
                "student_info": "Người đi làm học để thi JLPT",
                "requirements": "Có chứng chỉ N3 hoặc tốt hơn",
                "mode": "online",
                "post_status": "inactive",
                "created_at": datetime.now(VN_TZ),
                "updated_at": datetime.now(VN_TZ),
            },
            {
                "creator_id": user_ids[0],
                "title": "Gia sư Lịch sử lớp 12 ôn thi đại học",
                "subject": "Lịch sử",
                "level": "12",
                "address": "TP. Hồ Chí Minh",
                "salary_amount": 160000.00,
                "sessions_per_week": 2,
                "minutes_per_session": 90,
                "preferred_times": "Sáng thứ 7 và Chủ nhật",
                "student_info": "Học sinh cần ôn gấp trước kì thi",
                "requirements": "Nắm chắc chương trình thi THPT QG",
                "mode": "offline",
                "post_status": "inactive",
                "created_at": datetime.now(VN_TZ),
                "updated_at": datetime.now(VN_TZ),
            },
            {
                "creator_id": user_ids[0],
                "title": "Gia sư Tin học văn phòng",
                "subject": "Tin học",
                "level": "Văn phòng",
                "address": "Online",
                "salary_amount": 180000.00,
                "sessions_per_week": 2,
                "minutes_per_session": 75,
                "preferred_times": "Buổi tối các ngày trong tuần",
                "student_info": "Người đi làm, cần học Excel và Word",
                "requirements": "Kinh nghiệm giảng dạy người mới",
                "mode": "online",
                "post_status": "inactive",
                "created_at": datetime.now(VN_TZ),
                "updated_at": datetime.now(VN_TZ),
            },
            {
                "creator_id": user_ids[0],
                "title": "Gia sư Vẽ mỹ thuật cơ bản",
                "subject": "Mỹ thuật",
                "level": "Cơ bản",
                "address": "Hà Nội",
                "salary_amount": 170000.00,
                "sessions_per_week": 1,
                "minutes_per_session": 120,
                "preferred_times": "Chiều Chủ nhật",
                "student_info": "Học sinh tiểu học yêu thích hội họa",
                "requirements": "Sinh viên hoặc giáo viên ngành Mỹ thuật",
                "mode": "offline",
                "post_status": "inactive",
                "created_at": datetime.now(VN_TZ),
                "updated_at": datetime.now(VN_TZ),
            },

        ]
        result = posts_collection.insert_many(posts_data)
        print("Posts inserted:", result.inserted_ids)
    else:
        print("Posts already exist.")

    # Lấy posts hiện có để dùng các bước sau
    posts = list(posts_collection.find({}))

    # ==========================
    # INIT APPLICATIONS
    # ==========================
    if applications_collection.count_documents({}) == 0:
        if len(user_ids) < 3:
            print("Not enough users for applications.")
            return

        applications_data = [
            {
                "post_id": posts[0]["_id"],
                "tutor_id": user_ids[2],
                "application_status": "pending",
                "applied_at": datetime.now(VN_TZ),
            },
            {
                "post_id": posts[1]["_id"],
                "tutor_id": user_ids[0],
                "application_status": "accepted",
                "applied_at": datetime.now(VN_TZ),
            },
            {
                "post_id": posts[1]["_id"],
                "tutor_id": user_ids[2],
                "application_status": "rejected",
                "applied_at": datetime.now(VN_TZ),
            },
            {
                "post_id": posts[4]["_id"],
                "tutor_id": user_ids[1],
                "application_status": "rejected",
                "applied_at": datetime.now(VN_TZ), 
            }
        ]
        applications_collection.insert_many(applications_data)
        print("Applications inserted!")
    else:
        print("Applications already exist.")

    # ==========================
    # INIT BOOKINGS
    # ==========================
    if bookings_collection.count_documents({}) == 0:
        if len(user_ids) < 3 or len(posts) < 2:
            print("Not enough users or posts for bookings.")
        else:
            bookings_data = [
                {
                    "post_id": posts[0]["_id"],
                    "tutor_id": user_ids[2],
                    "parent_id": user_ids[0],
                    "start_date": datetime.now(VN_TZ) + timedelta(days=1),
                    "end_date": datetime.now(VN_TZ) + timedelta(days=30),
                    "contract_status": "pending",
                    "created_at": datetime.now(VN_TZ),
                    "updated_at": datetime.now(VN_TZ),
                },
                {
                    "post_id": posts[1]["_id"],
                    "tutor_id": user_ids[0],
                    "parent_id": user_ids[1],
                    "start_date": datetime.now(VN_TZ) + timedelta(days=2),
                    "end_date": datetime.now(VN_TZ) + timedelta(days=32),
                    "contract_status": "accepted",
                    "created_at": datetime.now(VN_TZ),
                    "updated_at": datetime.now(VN_TZ),
                },
            ]
            bookings_collection.insert_many(bookings_data)
            print("Bookings inserted!")
    else:
        print("Bookings already exist.")

    # ==========================
    # INIT TRANSACTIONS
    # ==========================
    if transactions_collection.count_documents({}) == 0:
        if len(posts) < 2:
            print("Not enough posts for transactions.")
            return

        transactions_data = [
            {
                "post_id": posts[0]["_id"],
                "payer_id": posts[0]["creator_id"],
                "amount_money": 10000.00,
                "transaction_status": "paid",
                "created_at": datetime.now(VN_TZ),
            },
            {
                "post_id": posts[1]["_id"],
                "payer_id": posts[1]["creator_id"],
                "amount_money": 10000.00,
                "transaction_status": "paid",
                "created_at": datetime.now(VN_TZ),
            },
        ]
        transactions_collection.insert_many(transactions_data)
        print("Transactions inserted!")
    else:
        print("Transactions already exist.")

    # ==========================
    # INIT RATINGS
    # ==========================
    try:
        has_ratings = ratings_collection.count_documents({}) > 0
    except Exception:
        has_ratings = False

    if not has_ratings:
        # create a few sample ratings between seeded users
        if len(user_ids) >= 3:
            ratings_data = [
                {
                    "tutor_id": user_ids[1],
                    "parent_id": user_ids[0],
                    "booking_id": None,
                    "rating": 5,
                    "comment": "Tuyệt vời, rất nhiệt tình",
                    "rated_at": datetime.now(VN_TZ),
                },
                {
                    "tutor_id": user_ids[1],
                    "parent_id": user_ids[2],
                    "booking_id": None,
                    "rating": 4,
                    "comment": "Khá tốt",
                    "rated_at": datetime.now(VN_TZ),
                },
                {
                    "tutor_id": user_ids[0],
                    "parent_id": user_ids[0],
                    "booking_id": None,
                    "rating": 5,
                    "comment": "Tuyệt vời, rất nhiệt tình",
                    "rated_at": datetime.now(VN_TZ),
                },
                {
                    "tutor_id": user_ids[0],
                    "parent_id": user_ids[2],
                    "booking_id": None,
                    "rating": 4,
                    "comment": "Khá tốt",
                    "rated_at": datetime.now(VN_TZ),
                },
                {
                    "tutor_id": user_ids[0],
                    "parent_id": user_ids[2],
                    "booking_id": None,
                    "rating": 4,
                    "comment": "Khá tốt",
                    "rated_at": datetime.now(VN_TZ),
                }
            ]
            try:
                ratings_collection.insert_many(ratings_data)
                print("Ratings inserted!")
            except Exception:
                print("Failed to insert ratings (DB may not support it).")
        else:
            print("Not enough users to create sample ratings.")
    else:
        print("Ratings already exist.")
