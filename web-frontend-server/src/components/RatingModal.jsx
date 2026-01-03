import React, { useState } from 'react';
import fetchWithAuth from '../api';
import './RatingModal.css';

export default function RatingModal({ tutorId, bookingId, token, onClose, onSubmitted }) {
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    setSubmitting(true);
    try {
      const resp = await fetchWithAuth('/api/rating/add-rating', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tutor_id: tutorId, booking_id: bookingId || null, rating, comment })
      }, token);
      if (!resp.ok) {
        alert('Gửi đánh giá thất bại: ' + JSON.stringify(resp.data));
      } else {
        onSubmitted?.();
        onClose();
      }
    } catch (err) {
      alert('Lỗi: ' + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="rating-modal-overlay" onClick={onClose}>
      <div className="rating-modal" onClick={e=>e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>✕</button>
        <h3>Đánh giá gia sư</h3>
        <div className="rating-stars">
          {[1,2,3,4,5].map(i => (
            <button key={i} className={i<=rating? 'star on':'star'} onClick={()=>setRating(i)}>{i<=rating? '★':'☆'}</button>
          ))}
        </div>
        <textarea placeholder="Ghi chú (tuỳ chọn)" value={comment} onChange={e=>setComment(e.target.value)} />
        <div className="rating-actions">
          <button className="btn btn-primary" onClick={submit} disabled={submitting}>{submitting? 'Đang gửi...':'Đồng ý'}</button>
          <button className="btn" onClick={onClose}>Hủy</button>
        </div>
      </div>
    </div>
  );
}
