import { useEffect, useState } from "react";
import { useAuth } from "../auth";
import fetchWithAuth from "../api";
import ApplicationList from "./ApplicationList";
import "./Center.css";

export default function Center() {
  const { token, user } = useAuth();
  const isAdmin = user?.role === "admin";
  const isVerifiedProfile = user?.status === 'accepted';
  const [filters, setFilters] = useState({ subject: "", level: "", address: "", mode: "" });
  const [posts, setPosts] = useState([]);
  const [skip, setSkip] = useState(0);
  const [limit, setLimit] = useState(6);
  const [totalFetched, setTotalFetched] = useState(0);
  // Admin always sees "all", customer can toggle between "me" and "all"
  const [viewMode, setViewMode] = useState("me");
  const effectiveViewMode = isAdmin ? "all" : viewMode;
  const [appliedPostIds, setAppliedPostIds] = useState(new Set());
  const [loadingApply, setLoadingApply] = useState({});
  const [deletingId, setDeletingId] = useState(null);

  async function loadPosts() {
    const params = new URLSearchParams();
    // Add scope to request: "me" or "all"
    params.set("scope", effectiveViewMode);
    params.set("skip", String(skip));
    params.set("limit", String(limit));
    if (filters.subject) params.append("subject", filters.subject);
    if (filters.level) params.append("level", filters.level);
    if (filters.address) params.append("address", filters.address);
    if (filters.mode) params.append("mode", filters.mode);

    const url = `/api/post/get-post?${params.toString()}`;
    const resp = await fetchWithAuth(url, { method: "GET" }, token);
    if (resp.ok && Array.isArray(resp.data)) {
      setPosts(resp.data);
      setTotalFetched(resp.data.length);
    } else {
      setPosts([]);
      setTotalFetched(0);
    }
  }

  async function loadAppliedPosts() {
    const resp = await fetchWithAuth("/api/application/me/get-application?skip=0&limit=100", { method: "GET" }, token);
    if (resp.ok && Array.isArray(resp.data)) {
      const postIds = new Set(resp.data.map(app => app.post_id));
      setAppliedPostIds(postIds);
    }
  }

  async function handleApply(postId) {
    if (!token) {
      alert("Please login to apply");
      return;
    }

    setLoadingApply(prev => ({ ...prev, [postId]: true }));
    try {
      const resp = await fetchWithAuth("/api/application/add-application", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ post_id: postId }),
      }, token);

      if (resp.ok) {
        alert("Application submitted successfully!");
        setAppliedPostIds(prev => new Set([...prev, postId]));
      } else {
        alert("Failed to submit application: " + JSON.stringify(resp.data));
      }
    } catch (error) {
      alert("Error submitting application: " + error.message);
    } finally {
      setLoadingApply(prev => ({ ...prev, [postId]: false }));
    }
  }

  async function deletePost(postId) {
    if (!token) {
      alert('Please login to delete posts');
      return;
    }
    if (!confirm('Bạn có chắc muốn xóa bài viết này?')) return;
    setDeletingId(postId);
    try {
      const resp = await fetchWithAuth('/api/post/delete-post', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: postId })
      }, token);

      if (resp.ok) {
        alert('Post deleted successfully');
        // reset to first page and reload
        setSkip(0);
        await loadPosts();
      } else {
        alert('Xóa thất bại: ' + JSON.stringify(resp.data));
      }
    } catch (err) {
      alert('Error deleting post: ' + (err.message || err));
    } finally {
      setDeletingId(null);
    }
  }

  useEffect(() => {
    loadPosts();
    if (effectiveViewMode === "all") {
      loadAppliedPosts();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [skip, limit, effectiveViewMode]);

  useEffect(() => {
    setSkip(0);
    const params = new URLSearchParams();
    params.set("scope", effectiveViewMode);
    params.set("skip", String(0));
    params.set("limit", String(limit));
    if (filters.subject)
      params.append("subject", filters.subject);
    if (filters.level)
      params.append("level", filters.level);
    if (filters.address)
      params.append("address", filters.address);
    if (filters.mode)
      params.append("mode", filters.mode);
    const url = `/api/post/get-post?${params.toString()}`;
    fetchWithAuth(url, { method: "GET" }, token).then(resp => {
      if (resp.ok && Array.isArray(resp.data)) {
        setPosts(resp.data);
        setTotalFetched(resp.data.length);
      } else {
        setPosts([]);
        setTotalFetched(0);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, effectiveViewMode, limit]);

  return (
    <main className="center">
      <div className="filter-bar">
        {!isAdmin && (
          <div className="view-mode">
            <label>
              <input type="radio" name="viewMode" value="me" checked={viewMode === "me"} onChange={() => setViewMode("me")} />
              My posts
            </label>
            <label>
              <input type="radio" name="viewMode" value="all" checked={viewMode === "all"} onChange={() => setViewMode("all")} />
              All posts
            </label>
          </div>
        )}
        <input placeholder="Subject" value={filters.subject} onChange={(e) => setFilters({ ...filters, subject: e.target.value })} />
        <input placeholder="Level" value={filters.level} onChange={(e) => setFilters({ ...filters, level: e.target.value })} />
        <input placeholder="Address" value={filters.address} onChange={(e) => setFilters({ ...filters, address: e.target.value })} />
        <select value={filters.mode} onChange={(e) => setFilters({ ...filters, mode: e.target.value })}>
          <option value="">All Modes</option>
          <option value="online">Online</option>
          <option value="offline">Offline</option>
        </select>
      </div>

      <div className="posts">
        {posts.length === 0 && <div className="muted">No posts found</div>}
        {posts.map((p) => (
          <div key={p.id || Math.random()} className="post-card">
            <div className="post-header">
              <div className="post-title-section">
                <h3>{p.title}</h3>
                {!isAdmin && effectiveViewMode === "me" && (
                  <>
                    <span className={`status-badge status-${p.post_status || "inactive"}`}>
                      {p.post_status === "active" ? "Active" : "Inactive"}
                    </span>
                    <button
                      className="btn btn-danger"
                      style={{ marginLeft: 8, padding: '6px 10px', fontSize: 12 }}
                      onClick={() => deletePost(p.id)}
                      disabled={deletingId === p.id}
                    >
                      {deletingId === p.id ? 'Deleting...' : 'Delete'}
                    </button>
                  </>
                )}
              </div>
            </div>

            <div className="post-meta-tags">
              <span className="tag">{p.subject}</span>
              <span className="tag">Grade {p.level}</span>
              <span className="tag mode-tag">{p.mode}</span>
            </div>

            <div className="post-content">
              <div className="post-section">
                <h4>Location & Schedule</h4>
                <p><strong>Address:</strong> {p.address}</p>
                <p><strong>Preferred Times:</strong> {p.preferred_times}</p>
                <p><strong>Sessions:</strong> {p.sessions_per_week} sessions/week, {p.minutes_per_session} minutes each</p>
              </div>

              <div className="post-section">
                <h4>Salary & Rate</h4>
                <p className="salary-highlight">💰 {p.salary_amount?.toLocaleString('vi-VN')} VND</p>
              </div>

              <div className="post-section">
                <h4>Student Information</h4>
                <p>{p.student_info}</p>
              </div>

              <div className="post-section">
                <h4>Requirements</h4>
                <p>{p.requirements}</p>
              </div>

              {!isAdmin && effectiveViewMode === "all" && (
                <div className="post-action">
                    {appliedPostIds.has(p.id) ? (
                      <button className="btn-applied" disabled>✓ Already Applied</button>
                    ) : (
                      <>
                        <button 
                          className="btn-apply" 
                          onClick={() => handleApply(p.id)}
                          disabled={loadingApply[p.id] || !isVerifiedProfile}
                        >
                          {loadingApply[p.id] ? "Submitting..." : (isVerifiedProfile ? "Apply Now" : "Profile not verified")}
                        </button>
                        {!isVerifiedProfile && (
                          <div style={{color:'#b91c1c', fontSize:12, marginTop:6}}>Only verified profiles can apply</div>
                        )}
                      </>
                    )}
                </div>
              )}

              {isAdmin && (
                <ApplicationList
                  postId={p.id}
                  token={token}
                  onApplicationUpdated={() => loadPosts()}
                />
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="pagination">
        <button onClick={() => setSkip(Math.max(0, skip - limit))} disabled={skip === 0}>Prev</button>
        <span>Showing {skip + 1} - {skip + totalFetched}</span>
        <button onClick={() => setSkip(skip + limit)} disabled={totalFetched < limit}>Next</button>
      </div>
    </main>
  );
}
