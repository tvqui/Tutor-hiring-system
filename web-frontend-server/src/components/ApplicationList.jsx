import { useState, useEffect } from "react";
import fetchWithAuth from "../api";
import TutorDetailModal from "./TutorDetailModal";
import "./ApplicationList.css";

export default function ApplicationList({ postId, token, onApplicationUpdated }) {
  const [applications, setApplications] = useState([]);
  const [tutors, setTutors] = useState({});
  const [loading, setLoading] = useState(false);
  const [selectedTutor, setSelectedTutor] = useState(null);
  const [showViewAll, setShowViewAll] = useState(false);

  useEffect(() => {
    loadApplications();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [postId]);

  async function loadApplications() {
    setLoading(true);
    try {
      const resp = await fetchWithAuth(
        `/api/application/get-application-by-post?skip=0&limit=100&application_status=pending`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ post_id: postId }),
        },
        token
      );

      if (resp.ok && Array.isArray(resp.data)) {
        setApplications(resp.data);
        // Load tutor info for each application
        resp.data.forEach(app => {
          loadTutorInfo(app.tutor_id);
        });
      }
    } catch (error) {
      console.error("Error loading applications:", error);
    } finally {
      setLoading(false);
    }
  }

  async function loadTutorInfo(tutorId) {
    try {
      const resp = await fetchWithAuth("/api/auth/get-profile-by-user-id", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: tutorId }),
      }, token);
      if (resp.ok) {
        setTutors(prev => ({ ...prev, [tutorId]: resp.data }));
      }
    } catch (error) {
      console.error("Error loading tutor info:", error);
    }
  }

  const pendingApps = applications.filter(app => app.application_status === "pending");
  const displayedApps = showViewAll ? pendingApps : pendingApps.slice(0, 5);

  return (
    <div className="applications-section">
      <div className="applications-header">
        <h4>Applicants ({pendingApps.length})</h4>
      </div>

      {loading ? (
        <div className="loading">Loading applicants...</div>
      ) : pendingApps.length === 0 ? (
        <div className="no-applicants">No applicants yet</div>
      ) : (
        <>
          <div className="applicants-grid">
            {displayedApps.map(app => {
              const tutor = tutors[app.tutor_id];
              if (!tutor) return null;
              const avg = tutor && tutor.avg_rating != null ? Number(tutor.avg_rating) : NaN;
              const avgValid = !isNaN(avg);
              return (
                <div key={app._id || app.id} className="applicant-card">
                  <div className="applicant-avatar">
                    {(tutor.display_name || tutor.username || "U").slice(0, 1).toUpperCase()}
                  </div>
                  <div className="applicant-info">
                    <p className="applicant-name">{tutor.display_name || tutor.username}</p>
                    {avgValid && (
                      <div className="tutor-rating">
                        <span className="stars">{renderStars(avg)}</span>
                        <span className="rating-meta">{avg.toFixed(2)} · ({tutor.rating_count || 0})</span>
                      </div>
                    )}
                    {tutor.gender && <p className="applicant-meta">{tutor.gender}</p>}
                    {tutor.subjects && tutor.subjects.length > 0 && (
                      <p className="applicant-subjects">{tutor.subjects.slice(0, 2).join(", ")}</p>
                    )}
                  </div>
                  <button
                    className="btn-view-detail"
                    onClick={() => setSelectedTutor({ tutor, application: app })}
                  >
                    View
                  </button>
                </div>
              );
            })}
          </div>

          {pendingApps.length > 5 && !showViewAll && (
            <button className="btn-view-all" onClick={() => setShowViewAll(true)}>
              View All ({pendingApps.length})
            </button>
          )}

          {showViewAll && (
            <button className="btn-view-less" onClick={() => setShowViewAll(false)}>
              Show Less
            </button>
          )}
        </>
      )}

      {selectedTutor && (
        <TutorDetailModal
          tutor={selectedTutor.tutor}
          application={selectedTutor.application}
          postId={postId}
          token={token}
          onClose={() => setSelectedTutor(null)}
          onAccept={() => {
            loadApplications();
            onApplicationUpdated?.();
          }}
          onReject={() => {
            loadApplications();
            onApplicationUpdated?.();
          }}
        />
      )}
    </div>
  );
}

// Helper to render star characters for a rating (0-5)
function renderStars(avg) {
  const full = Math.floor(avg);
  const half = avg - full >= 0.5 ? 1 : 0;
  const empty = 5 - full - half;
  return '★'.repeat(full) + (half ? '☆' : '') + '☆'.repeat(empty);
}
