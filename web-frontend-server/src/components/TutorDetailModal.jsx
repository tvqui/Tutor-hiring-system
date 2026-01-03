import { useState, useEffect } from "react";
import fetchWithAuth from "../api";
import "./TutorDetailModal.css";

export default function TutorDetailModal({ tutor, application, postId, token, onClose, onAccept, onReject }) {
  const [bookingForm, setBookingForm] = useState({
    start_date: "",
    end_date: "",
  });
  const [showBooking, setShowBooking] = useState(false);
  const [bookingCreated, setBookingCreated] = useState(false);
  const [isAccepting, setIsAccepting] = useState(false);
  const [isCreatingBooking, setIsCreatingBooking] = useState(false);
  const [certificates, setCertificates] = useState([]);
  const [certificatesLoading, setCertificatesLoading] = useState(false);
  const [ratings, setRatings] = useState([]);
  const [ratingsLoading, setRatingsLoading] = useState(false);
  const [postCreator, setPostCreator] = useState(null);

  useEffect(() => {
    const userId = tutor && (tutor._id || tutor.id);
    if (userId) {
      loadCertificates(userId);
    }
  }, [tutor?._id, tutor?.id]);

  useEffect(() => {
    const userId = tutor && (tutor._id || tutor.id);
    if (!userId) return;
    let mounted = true;
    async function loadRatings() {
      setRatingsLoading(true);
      try {
        const resp = await fetchWithAuth(`/api/rating/tutor/${userId}/ratings`, { method: 'GET' }, token);
        if (mounted && resp.ok && Array.isArray(resp.data)) {
          setRatings(resp.data);
        } else if (mounted) {
          setRatings([]);
        }
      } catch (err) {
        console.error('Failed to load ratings for tutor', userId, err);
        if (mounted) setRatings([]);
      } finally {
        if (mounted) setRatingsLoading(false);
      }
    }
    loadRatings();
    return () => (mounted = false);
  }, [tutor?._id, tutor?.id, token]);

  useEffect(() => {
    if (!postId) return;
    let mounted = true;
    async function loadPostCreator() {
      try {
        const resp = await fetchWithAuth(`/api/post/${postId}`, { method: 'GET' }, token);
        if (mounted && resp.ok && resp.data) {
          // Fetch post creator info
          const creatorResp = await fetchWithAuth('/api/auth/get-profile-by-user-id', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: resp.data.creator_id }),
          }, token);
          if (mounted && creatorResp.ok) {
            setPostCreator(creatorResp.data);
          }
        }
      } catch (err) {
        console.error('Failed to load post creator', err);
      }
    }
    loadPostCreator();
    return () => (mounted = false);
  }, [postId, token]);

  // normalize tutor avg rating (backend may return string/Decimal)
  const avg = tutor && tutor.avg_rating != null ? Number(tutor.avg_rating) : NaN;

  const loadCertificates = async (tutorId) => {
    setCertificatesLoading(true);
    try {
      const resp = await fetchWithAuth("/api/auth/get-certificate-by-user-id", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: tutorId }),
      }, token);

      if (resp.ok && resp.data) {
        setCertificates(Array.isArray(resp.data) ? resp.data : [resp.data]);
      }
    } catch (error) {
      console.log("Error loading certificates:", error);
    } finally {
      setCertificatesLoading(false);
    }
  };

  const handleAccept = async () => {
    // Instead of calling accept immediately, open the booking form so parent can set details
    if (!application) return;
    setShowBooking(true);
  };

  const handleReject = async () => {
    if (!application) return;
    try {
      const resp = await fetchWithAuth("/api/application/update-status", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: application._id || application.id,
          application_status: "rejected",
        }),
      }, token);

      if (resp.ok) {
        alert("Application rejected!");
        if (onReject) onReject(); 
        onClose();
        // Reload page to refresh the application list and remove rejected application
        window.location.reload();
      } else {
        alert("Failed to reject: " + JSON.stringify(resp.data));
      }
    } catch (error) {
      alert("Error: " + error.message);
    }
  };

  const handleCreateBooking = async () => {
    if (!bookingForm.start_date || !bookingForm.end_date) {
      alert("Please fill in all date fields");
      return;
    }

    setIsCreatingBooking(true);
    try {
      const resp = await fetchWithAuth("/api/booking/add-booking", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          post_id: postId,
          tutor_id: tutor._id || tutor.id,
          start_date: bookingForm.start_date,
          end_date: bookingForm.end_date,
        }),
      }, token);

      if (resp.ok) {
        alert("Booking created successfully! Email will be sent to tutor.");
        // After booking is created, finalize acceptance: update application status and activate post
        try {
          const appResp = await fetchWithAuth("/api/application/update-status", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id: application._id || application.id, application_status: "accepted" }),
          }, token);

          if (!appResp.ok) {
            alert("Booking created but failed to update application status: " + JSON.stringify(appResp.data));
          }
        } catch (err) {
          console.error('Failed to update application status after booking', err);
          alert('Booking created but failed to update application status');
        }

        // Activate post
        try {
          const postResp = await fetchWithAuth("/api/post/update-status", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id: postId, post_status: "active" }),
          }, token);
          if (!postResp.ok) {
            alert("Booking created but failed to activate post: " + JSON.stringify(postResp.data));
          }
        } catch (err) {
          console.error('Failed to activate post after booking', err);
        }

        setShowBooking(false);
        setBookingForm({ start_date: "", end_date: "" });
        setBookingCreated(true);
        if (onAccept) onAccept();
        onClose();
      } else {
        alert("Failed to create booking: " + JSON.stringify(resp.data));
      }
    } catch (error) {
      alert("Error: " + error.message);
    } finally {
      setIsCreatingBooking(false);
    }
  };

  // Extend end_date by given days (default 30)
  function extendEndDate(days = 30) {
    // prefer existing end_date, otherwise fall back to start_date, otherwise use today
    const base = bookingForm.end_date || bookingForm.start_date || new Date().toISOString().slice(0,10);
    // parse base (YYYY-MM-DD) into Date
    const parts = base.split('-').map(p => Number(p));
    const dateObj = new Date(parts[0], (parts[1]||1) - 1, parts[2] || 1);
    dateObj.setDate(dateObj.getDate() + days);
    const yyyy = dateObj.getFullYear();
    const mm = String(dateObj.getMonth() + 1).padStart(2, '0');
    const dd = String(dateObj.getDate()).padStart(2, '0');
    setBookingForm(prev => ({ ...prev, end_date: `${yyyy}-${mm}-${dd}` }));
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>✕</button>

        {!showBooking ? (
          <>
            <div className="tutor-header">
              <div className="tutor-avatar">
                {(tutor.display_name || tutor.username || "U").slice(0, 1).toUpperCase()}
              </div>
              <div className="tutor-basic-info">
                          <h2>{tutor.display_name || tutor.username}</h2>
                          <div style={{display:'flex', alignItems:'center', gap:8}}>
                            {Number.isFinite(avg) && (
                              <>
                                <span className="tutor-stars">{renderStars(avg)}</span>
                                <span className="tutor-rating-meta">{avg.toFixed(2)} · ({tutor.rating_count || 0})</span>
                              </>
                            )}
                          </div>
                          <p className="tutor-email">{tutor.email}</p>
              </div>
            </div>

            <div className="tutor-details">
              <div className="detail-group">
                <h4>Personal Information</h4>
                {tutor.phone && <p><strong>Phone:</strong> {tutor.phone}</p>}
                {tutor.gender && <p><strong>Gender:</strong> {tutor.gender}</p>}
                {tutor.address && <p><strong>Address:</strong> {tutor.address}</p>}
              </div>

              <div className="detail-group">
                <h4>Expertise</h4>
                {tutor.subjects && tutor.subjects.length > 0 && (
                  <p><strong>Subjects:</strong> {tutor.subjects.join(", ")}</p>
                )}
                {tutor.levels && tutor.levels.length > 0 && (
                  <p><strong>Levels:</strong> {tutor.levels.join(", ")}</p>
                )}
              </div>

              {tutor.bio && (
                <div className="detail-group">
                  <h4>Bio</h4>
                  <p>{tutor.bio}</p>
                </div>
              )}

              <div className="detail-group">
                <h4>Certificates</h4>
                {certificatesLoading ? (
                  <p>Loading certificates...</p>
                ) : certificates.length > 0 ? (
                  <ul className="certificates-list">
                    {certificates.map((cert, idx) => (
                        // Display certificate details
                      <li key={idx} className="cert-item"> 
                        <div className="cert-header">
                          <strong>{cert.certificate_type || cert.certificate_name || cert.name || "Certificate"}</strong>
                          {cert.uploaded_at && (
                            <span className="cert-date"> - {new Date(cert.uploaded_at).toLocaleDateString('vi-VN')}</span>
                          )}
                        </div>
                        {cert.description && <div className="cert-desc">{cert.description}</div>}
                        {cert.filename && !cert.url && (
                          <div className="cert-file">File: {cert.filename}</div>
                        )}
                        {cert.url && (
                          <div className="cert-link-wrap">
                            <a className="cert-link" href={cert.url} target="_blank" rel="noreferrer">View file</a>
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>No certificates available</p>
                )}
              </div>

              <div className="detail-group">
                <h4>Ratings</h4>
                {ratingsLoading ? (
                  <p>Loading ratings...</p>
                ) : ratings && ratings.length > 0 ? (
                  <div className="rating-list">
                    {ratings.map((r) => (
                      <div className="rating-item" key={r.id || r._id || Math.random()}>
                        <div className="rating-top" style={{display:'flex', alignItems:'center', justifyContent:'space-between'}}>
                          <div style={{display:'flex', alignItems:'center', gap:8}}>
                            <span className="rating-stars">{renderStars(Number(r.rating || 0))}</span>
                            <strong className="rating-who">{postCreator?.display_name || postCreator?.username || 'Post Creator'}</strong>
                          </div>
                          <div className="rating-meta">{r.rated_at ? new Date(r.rated_at).toLocaleString() : ''}</div>
                        </div>
                        {r.comment && <div className="rating-comment">{r.comment}</div>}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p>No ratings yet</p>
                )}
              </div>

              {application && application.application_status === "pending" && application.application_status !== "rejected" && (
                <div className="application-actions">
                  <button className="btn-accept" onClick={handleAccept} disabled={isAccepting}>
                    {isAccepting ? "Processing..." : "✓ Accept"}
                  </button>
                  <button className="btn-reject" onClick={handleReject}>
                    ✕ Reject
                  </button>
                </div>
              )}
            </div>
          </>
        ) : (
          !bookingCreated && (
            <div className="booking-form">
              <h3>Create Booking Contract</h3>
              <p className="booking-tutor">Tutor: <strong>{tutor.display_name || tutor.username}</strong></p>
              <div className="form-group">
                <label>Start Date:</label>
                <input
                  type="date"
                  value={bookingForm.start_date}
                  onChange={(e) => setBookingForm({ ...bookingForm, start_date: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>End Date:</label>
                <div style={{display: 'flex', gap: 8, alignItems: 'center'}}>
                  <input
                    type="date"
                    value={bookingForm.end_date}
                    onChange={(e) => setBookingForm({ ...bookingForm, end_date: e.target.value })}
                  />
                  <button type="button" className="btn btn-secondary" onClick={() => extendEndDate(30)} title="Extend end date by 30 days">+30d</button>
                </div>
              </div>
              <div className="booking-actions">
                <button className="btn-create" onClick={handleCreateBooking} disabled={isCreatingBooking}>
                  {isCreatingBooking ? "Creating..." : "Create Booking"}
                </button>
                
                <button className="btn-cancel" onClick={() => setShowBooking(false)}>
                  Back
                </button>
              </div>
            </div>
          )
        )}
      </div>
    </div>
  );
}

// simple star renderer
function renderStars(avg) {
  const full = Math.floor(avg);
  const half = avg - full >= 0.5 ? 1 : 0;
  const empty = 5 - full - half;
  return '★'.repeat(full) + (half ? '☆' : '') + '☆'.repeat(empty);
}
