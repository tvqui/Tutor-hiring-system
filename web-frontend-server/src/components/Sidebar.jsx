import { useEffect, useState } from "react";
import { useAuth } from "../auth";
import fetchWithAuth from "../api";
import "./Sidebar.css";

export default function Sidebar({ onCreatePost }) {
  const { token, logout } = useAuth();
  const [profile, setProfile] = useState(null);
  const [txs, setTxs] = useState([]);
  const [hoveringDetails, setHoveringDetails] = useState(false);

  // normalize avg rating coming from backend (could be number, string, or Decimal-like)
  const profileAvg = profile && profile.avg_rating != null ? Number(profile.avg_rating) : NaN;

  useEffect(() => {
    let mounted = true;
    async function loadProfile() {
      if (!token) return setProfile(null);
      const resp = await fetchWithAuth("/api/auth/me/get-profile", { method: "GET" }, token);
      if (mounted && resp.ok) setProfile(resp.data);
    }
    loadProfile();
    return () => (mounted = false);
  }, [token]);

  useEffect(() => {
    let mounted = true;
    async function loadTransactions() {
      if (!token) return setTxs([]);
      const resp = await fetchWithAuth("/api/transaction/me/get-transaction?skip=0&limit=20", { method: "GET" }, token);
      if (mounted && resp.ok && Array.isArray(resp.data)) setTxs(resp.data);
    }
    loadTransactions();
    return () => (mounted = false);
  }, [token]);

  return (
    <aside className="sidebar">
      <div className="profile-card">
        {profile ? (
          <>
            <div className="card-header"></div>
            
            <div className="avatar-holder">
              <div className="avatar-initial">
                {(profile.display_name || profile.username || "U").slice(0,1).toUpperCase()}
              </div>
            </div>

            <div className="profile-name">
              <h3>{profile.display_name || profile.username}</h3>
            </div>

            <div className="profile-details" onMouseEnter={()=>setHoveringDetails(true)} onMouseLeave={()=>setHoveringDetails(false)}>
              {Number.isFinite(profileAvg) && (
                <div className="profile-rating detail-item">
                  <span className="stars">{renderStars(profileAvg)}</span>
                  <span style={{marginLeft:8}}>{profileAvg.toFixed(2)} · ({profile.rating_count || 0})</span>
                </div>
              )}
              {/* {profile.email && <div className="detail-item"><strong>Email:</strong> {profile.email}</div>}
              {profile.phone && <div className="detail-item"><strong>Phone:</strong> {profile.phone}</div>}
              {profile.gender && <div className="detail-item"><strong>Gender:</strong> {profile.gender}</div>}
              {profile.address && <div className="detail-item"><strong>Address:</strong> {profile.address}</div>} */}
              {profile.subjects && profile.subjects.length > 0 && (
                <div className="detail-item"><strong>Subjects:</strong> {profile.subjects.join(", ")}</div>
              )}
              {profile.levels && profile.levels.length > 0 && (
                <div className="detail-item"><strong>Levels:</strong> {profile.levels.join(", ")}</div>
              )}
              {hoveringDetails && (
                <div className="detail-hover-btn">
                  <button className="btn btn-secondary" onClick={()=>window.location.hash = '#profile'}>View details</button>
                </div>
              )}
            </div>

            <div className="profile-actions">
              <button className="btn btn-secondary" onClick={() => window.location.hash = '#center'}>
                🏠 Home
              </button>
              <button className="btn btn-secondary" onClick={() => window.location.hash = '#applications'}>
                📨 Applications
              </button>
              {profile && profile.role === 'admin' && (
                <button className="btn btn-secondary" onClick={() => window.location.hash = '#verify'}>
                  ✅ Verify
                </button>
              )}
              <button onClick={() => window.location.hash = '#create-post'} className="btn btn-primary">Create Post</button>
              <button className="btn btn-secondary" onClick={() => window.location.hash = '#bookings'}>
                📋 Bookings
              </button>
              <button onClick={logout} className="btn btn-secondary">Logout</button>
            </div>

            <div className="transaction-section">
              <h4>Transaction History</h4>
              <div className="transactions-list">
                {txs.length === 0 && <div className="empty-state">No transactions</div>}
                {txs.map((t) => (
                  <div className="tx-item" key={t.id || Math.random()}>
                    <div className="tx-amount">{t.amount_money?.toLocaleString('vi-VN')} VND</div>
                    <div className="tx-status">{t.transaction_status}</div>
                    <div className="tx-date">{new Date(t.created_at || "").toLocaleString()}</div>
                  </div>
                ))}
              </div>
            </div>
          </>
        ) : (
          <div className="login-prompt">
            <p>Please login to view profile</p>
            <button onClick={logout} className="btn btn-secondary">Logout</button>
          </div>
        )}
      </div>
    </aside>
  );
}

// helper to render stars (0-5)
function renderStars(avg) {
  const full = Math.floor(avg);
  const half = avg - full >= 0.5 ? 1 : 0;
  const empty = 5 - full - half;
  return '★'.repeat(full) + (half ? '☆' : '') + '☆'.repeat(empty);
}
