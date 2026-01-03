from fastapi import FastAPI, HTTPException, Security, status, Body
from fastapi.security import OAuth2PasswordBearer
from typing import List
from datetime import datetime, timezone
from bson import ObjectId

from shared.database import ratings_collection, users_collection, bookings_collection
from models import RatingModel, AddRatingModel, UpdateRatingModel, DelRatingModel
from jwt_utils import get_current_user

app = FastAPI(title="Rating Service", version="1.0.0", root_path="/api/rating")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def to_output(doc):
    return {
        'id': str(doc.get('_id')),
        'tutor_id': str(doc.get('tutor_id')),
        'parent_id': str(doc.get('parent_id')),
        'booking_id': str(doc.get('booking_id')) if doc.get('booking_id') else None,
        'rating': int(doc.get('rating')),
        'comment': doc.get('comment'),
        'rated_at': doc.get('rated_at')
    }


@app.post('/add-rating', response_model=RatingModel, status_code=status.HTTP_201_CREATED)
async def add_rating(input_data: AddRatingModel = Body(...), token: str = Security(oauth2_scheme)):
    current_user = await get_current_user(token=token, users_collection=users_collection)
    parent_id = current_user.id

    # validate tutor exists
    try:
        tutor_obj = users_collection.find_one({'_id': ObjectId(input_data.tutor_id)})
    except Exception:
        tutor_obj = None
    if not tutor_obj:
        raise HTTPException(status_code=404, detail='Tutor not found')

    # optional: validate booking exists
    if input_data.booking_id:
        try:
            booking_obj = bookings_collection.find_one({'_id': ObjectId(input_data.booking_id)})
        except Exception:
            booking_obj = None
        if not booking_obj:
            raise HTTPException(status_code=404, detail='Booking not found')

    doc = {
        'tutor_id': ObjectId(input_data.tutor_id),
        'parent_id': ObjectId(parent_id),
        'booking_id': ObjectId(input_data.booking_id) if input_data.booking_id else None,
        'rating': int(input_data.rating),
        'comment': input_data.comment,
        'rated_at': datetime.now(timezone.utc)
    }

    result = ratings_collection.insert_one(doc)
    saved = ratings_collection.find_one({'_id': result.inserted_id})
    return to_output(saved)


@app.post('/update-rating', response_model=RatingModel)
async def update_rating(input_data: UpdateRatingModel = Body(...), token: str = Security(oauth2_scheme)):
    current_user = await get_current_user(token=token, users_collection=users_collection)
    parent_id = current_user.id

    try:
        rating_doc = ratings_collection.find_one({'_id': ObjectId(input_data.id)})
    except Exception:
        rating_doc = None
    if not rating_doc:
        raise HTTPException(status_code=404, detail='Rating not found')

    # Only parent who created the rating can update
    if str(rating_doc.get('parent_id')) != parent_id:
        raise HTTPException(status_code=403, detail='Not allowed to update this rating')

    update_data = {}
    if input_data.rating is not None:
        update_data['rating'] = int(input_data.rating)
    if input_data.comment is not None:
        update_data['comment'] = input_data.comment

    if not update_data:
        raise HTTPException(status_code=400, detail='No fields to update')

    ratings_collection.update_one({'_id': ObjectId(input_data.id)}, {'$set': update_data})
    updated = ratings_collection.find_one({'_id': ObjectId(input_data.id)})
    return to_output(updated)


@app.post('/delete-rating', status_code=status.HTTP_200_OK)
async def delete_rating(input_data: DelRatingModel = Body(...), token: str = Security(oauth2_scheme)):
    current_user = await get_current_user(token=token, users_collection=users_collection)
    parent_id = current_user.id

    try:
        rating_doc = ratings_collection.find_one({'_id': ObjectId(input_data.id)})
    except Exception:
        rating_doc = None
    if not rating_doc:
        raise HTTPException(status_code=404, detail='Rating not found')

    if str(rating_doc.get('parent_id')) != parent_id:
        raise HTTPException(status_code=403, detail='Not allowed to delete this rating')

    ratings_collection.delete_one({'_id': ObjectId(input_data.id)})
    return {'message': 'Rating deleted successfully'}


@app.get('/tutor/{tutor_id}/ratings', response_model=List[RatingModel])
async def get_ratings_for_tutor(tutor_id: str, token: str = Security(oauth2_scheme)):
    # token only to ensure requester is authenticated
    _ = await get_current_user(token=token, users_collection=users_collection)

    try:
        cursor = ratings_collection.find({'tutor_id': ObjectId(tutor_id)}).sort('rated_at', -1)
    except Exception:
        raise HTTPException(status_code=400, detail='Invalid tutor id')

    items = [to_output(d) for d in cursor]
    return items


@app.get('/health')
async def health_check():
    return {"status": "ok"}