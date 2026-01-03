import { useState, useEffect } from "react";
import { useAuth } from "../auth";
import fetchWithAuth from "../api";
import RatingModal from "./RatingModal";
import "./Bookings.css";

export default function Bookings() {
  const { token, user } = useAuth();
  const [currentUserId, setCurrentUserId] = useState(null);
  const [bookings, setBookings] = useState([]);
  const [scope, setScope] = useState("parent");
  const [loading, setLoading] = useState(false);
  const [postDetails, setPostDetails] = useState({});
  const [tutorDetails, setTutorDetails] = useState({});
  const [parentDetails, setParentDetails] = useState({});
  const [ratingsByTutor, setRatingsByTutor] = useState({});
  const [showRatingFor, setShowRatingFor] = useState(null); // booking id being rated
  const [lastActionedBookings, setLastActionedBookings] = useState({}); // id -> status

  useEffect(() => {
    loadBookings();
    // load current user id for permission checks (who can rate)
    (async function loadProfile(){
      if (!token) return setCurrentUserId(null);
      try {
        const resp = await fetchWithAuth('/api/auth/me/get-profile', { method: 'GET' }, token);
        if (resp.ok && resp.data) setCurrentUserId(resp.data.id || resp.data._id || null);
      } catch (err) {
        console.error('Failed to load profile for bookings:', err);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scope]);

  async function loadBookings() {
    setLoading(true);
    try {
      const resp = await fetchWithAuth(
        `/api/booking/me/get-booking?scope=${scope}&skip=0&limit=100`,
        { method: "GET" },
        token
      );

      if (resp.ok && Array.isArray(resp.data)) {
        setBookings(resp.data);
        // Load related details
        resp.data.forEach(booking => {
          loadPostDetails(booking.post_id);
          loadTutorDetails(booking.tutor_id);
          if (booking.parent_id) loadParentDetails(booking.parent_id);
        });
      }
    } catch (error) {
      console.error("Error loading bookings:", error);
    } finally {
      setLoading(false);
    }
  }

  async function loadPostDetails(postId) {
    try {
      const resp = await fetchWithAuth(`/api/post/${postId}`, { method: "GET" }, token);
      if (resp.ok) {
        setPostDetails(prev => ({ ...prev, [postId]: resp.data }));
      }
    } catch (error) {
      console.error("Error loading post details:", error);
    }
  }

  async function loadTutorDetails(tutorId) {
    try {
      const resp = await fetchWithAuth("/api/auth/get-profile-by-user-id", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: tutorId }),
      }, token);
      if (resp.ok) {
        setTutorDetails(prev => ({ ...prev, [tutorId]: resp.data }));
        // also load ratings for this tutor (if not already loaded)
        if (!ratingsByTutor[tutorId]) await loadRatingsForTutor(tutorId);
      }
    } catch (error) {
      console.error("Error loading tutor details:", error);
    }
  }

  async function loadRatingsForTutor(tutorId) {
    if (!token) return;
    try {
      const resp = await fetchWithAuth(`/api/rating/tutor/${tutorId}/ratings`, { method: 'GET' }, token);
      if (resp.ok && Array.isArray(resp.data)) {
        setRatingsByTutor(prev => ({ ...prev, [tutorId]: resp.data }));
      } else {
        setRatingsByTutor(prev => ({ ...prev, [tutorId]: [] }));
      }
    } catch (err) {
      console.error('Error loading ratings for tutor', tutorId, err);
      setRatingsByTutor(prev => ({ ...prev, [tutorId]: [] }));
    }
  }

  async function loadParentDetails(parentId) {
    try {
      const resp = await fetchWithAuth("/api/auth/get-profile-by-user-id", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: parentId }),
      }, token);
      if (resp.ok) {
        setParentDetails(prev => ({ ...prev, [parentId]: resp.data }));
      }
    } catch (error) {
      console.error("Error loading parent details:", error);
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case "active":
        return "status-active";
      case "pending":
        return "status-pending";
      case "completed":
        return "status-completed";
      case "cancelled":
        return "status-cancelled";
      default:
        return "status-default";
    }
  };

  // simple star renderer for integer ratings 1-5
  function renderStars(avg) {
    const full = Math.floor(Number(avg) || 0);
    const empty = 5 - full;
    return '★'.repeat(Math.max(0, full)) + '☆'.repeat(Math.max(0, empty));
  }

  return (
    <main className="bookings-page">
      <div className="bookings-header">
        <h1>My Bookings</h1>
        <div className="scope-selector">
          <button
            className={scope === "parent" ? "active" : ""}
            onClick={() => setScope("parent")}
          >
            As Parent
          </button>
          <button
            className={scope === "tutor" ? "active" : ""}
            onClick={() => setScope("tutor")}
          >
            As Tutor
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading-state">Loading bookings...</div>
      ) : bookings.length === 0 ? (
        <div className="empty-state">
          <p>No bookings found</p>
          <p className="empty-subtitle">
            {scope === "parent"
              ? "You don't have any bookings as a parent yet"
              : "You don't have any bookings as a tutor yet"}
          </p>
        </div>
      ) : (
        <div className="bookings-list">
          {bookings.map((booking) => {
            const post = postDetails[booking.post_id];
            const tutor = tutorDetails[booking.tutor_id];
            const parent = parentDetails[booking.parent_id];

            const actionStatus = booking.contract_status;
 
            return (
              <div key={booking._id || booking.id} className={`booking-card ${getStatusColor(booking.contract_status)}`}>
                <div className="booking-card-header">
                  <div className="booking-title">
                    <h3>{post?.title || "Loading..."}</h3>
                    <span className={`booking-status ${booking.contract_status}`}>
                      {booking.contract_status === "accepted" && "🟢 Accepted"}
                      {booking.contract_status === "pending" && "🟡 Pending"}
                      {booking.contract_status === "completed" && "✅ Completed"}
                      {booking.contract_status === "cancelled" && "❌ Cancelled"}
                    </span>
                  </div>
                  {post && (
                    <div className="booking-meta">
                      <span className="meta-tag">{post.subject}</span>
                      <span className="meta-tag">Grade {post.level}</span>
                      <span className="meta-tag">{post.mode}</span>
                    </div>
                  )}
                </div>

                <div className="booking-content">
                  <div className="booking-section">
                    <h4>Contract Period</h4>
                    <p>
                      <strong>Start:</strong> {new Date(booking.start_date).toLocaleDateString('vi-VN')}
                    </p>
                    <p>
                      <strong>End:</strong> {new Date(booking.end_date).toLocaleDateString('vi-VN')}
                    </p>
                  </div>

                  <div className="booking-section">
                    <h4>{scope === "parent" ? "Tutor" : "Parent"}</h4>
                    {scope === "parent" && tutor ? (
                      <>
                        <p><strong>Name:</strong> {tutor.display_name || tutor.username}</p>
                        {tutor.email && <p><strong>Email:</strong> {tutor.email}</p>}
                        {tutor.phone && <p><strong>Phone:</strong> {tutor.phone}</p>}
                      </>
                    ) : scope === "tutor" && parent ? (
                      <>
                        <p><strong>Name:</strong> {parent.display_name || parent.username}</p>
                        {parent.email && <p><strong>Email:</strong> {parent.email}</p>}
                        {parent.phone && <p><strong>Phone:</strong> {parent.phone}</p>}
                      </>
                    ) : (
                      <p>Loading...</p>
                    )}
                  </div>

                  {post && (
                    <div className="booking-section">
                      <h4>Session Details</h4>
                      <p>
                        <strong>Sessions/Week:</strong> {post.sessions_per_week}
                      </p>
                      <p>
                        <strong>Minutes/Session:</strong> {post.minutes_per_session}
                      </p>
                      <p>
                        <strong>Salary:</strong> {post.salary_amount?.toLocaleString('vi-VN')} VND
                      </p>
                    </div>
                  )}
                </div>

                <div className="booking-footer">
                  <p className="booking-dates">
                    Created: {new Date(booking.created_at).toLocaleString('vi-VN')}
                  </p>

                  <div className="booking-actions-row">
                    {actionStatus !== 'completed' && actionStatus !== 'cancelled' && actionStatus !== 'pending'? (
                      // Only parents can Complete/Cancel
                      scope === 'parent' ? (
                        <>
                          <button className="btn btn-primary" onClick={async ()=>{
                            const id = booking._id || booking.id;
                            const resp = await fetchWithAuth('/api/booking/update-status', {
                              method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id, contract_status: 'completed' })
                            }, token);
                            if (resp.ok) {
                              // refresh bookings from server
                              await loadBookings();
                            } else {
                              alert('Failed to mark completed: '+JSON.stringify(resp.data));
                            }
                          }}>Complete</button>
                          <button className="btn btn-danger" onClick={async ()=>{
                            const id = booking._id || booking.id;
                            const resp = await fetchWithAuth('/api/booking/update-status', {
                              method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id, contract_status: 'cancelled' })
                            }, token);
                            if (resp.ok) {
                              // refresh bookings from server
                              await loadBookings();
                            } else {
                              alert('Failed to cancel: '+JSON.stringify(resp.data));
                            }
                          }}>Cancel</button>
                        </>
                      ) : null
                    ) : (
                      <>
                        {/* show Rate only to parent of the booking and only in parent view */}
                        {actionStatus == 'completed' && scope === 'parent' && currentUserId && (currentUserId === (booking.parent_id || booking.parentId || booking.parent)) && (
                          <button className="btn btn-secondary" onClick={()=>setShowRatingFor(booking._id || booking.id)}>Rate Tutor</button>
                        )}
                      </>
                    )}
                  </div>

                  {/* Ratings display */}
                  <div className="booking-ratings">
                    {/* {scope === 'parent' && currentUserId && (() => {
                      const tutorId = booking.tutor_id;
                      const bookingId = booking._id || booking.id;
                      const ratings = ratingsByTutor[tutorId] || [];
                      const myRatings = ratings.filter(r => (r.parent_id === currentUserId) && (r.booking_id === bookingId || !r.booking_id));
                      if (myRatings.length === 0) return null;
                      return (
                        <div className="my-ratings">
                          <h4>Your ratings for this tutor</h4>
                          {myRatings.map(r => (
                            <div key={r.id} className="rating-item">
                              <div className="rating-stars">{renderStars(r.rating)}</div>
                              {r.comment && <div className="rating-comment">{r.comment}</div>}
                              <div className="rating-meta">{new Date(r.rated_at).toLocaleString()}</div>
                            </div>
                          ))}
                        </div>
                      );
                    })()} */}

                    {scope === 'tutor' && (() => {
                      const tutorId = booking.tutor_id;
                      const ratings = ratingsByTutor[tutorId] || [];
                      if (ratings.length === 0) return null;
                      return (
                        <div className="tutor-ratings">
                          <h4>Ratings for you</h4>
                          {ratings.map(r => (
                            <div key={r.id} className="rating-item">
                              <div className="rating-stars">{renderStars(r.rating)}</div>
                              {r.comment && <div className="rating-comment">{r.comment}</div>}
                              <div className="rating-meta">{new Date(r.rated_at).toLocaleString()}</div>
                            </div>
                          ))}
                        </div>
                      );
                    })()}
                  </div>

                </div>
              </div>
            );
          })}
        </div>
      )}
      {showRatingFor && (()=>{
        const booking = bookings.find(b=> (b._id||b.id) === showRatingFor);
        const tutorId = booking?.tutor_id;
        const bookingId = booking?._id || booking?.id;
        return (
          <RatingModal token={token} tutorId={tutorId} bookingId={bookingId} onClose={()=>setShowRatingFor(null)} onSubmitted={()=>{/* optionally refresh bookings/tutor info */}} />
        );
      })()}
    </main>
  );
}
