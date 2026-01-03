import { useEffect, useState } from "react";
import fetchWithAuth from "../api";
import "./ApplicationList.css";

export default function Applications() {
  const [token] = [localStorage.getItem('token')];
  const [applications, setApplications] = useState([]);
  const [posts, setPosts] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      try {
        const resp = await fetchWithAuth('/api/application/me/get-application', { method: 'GET' }, token);
        if (mounted && resp.ok && Array.isArray(resp.data)) {
          setApplications(resp.data);
          // Load post titles for each application
          resp.data.forEach(app => {
            loadPostTitle(app.post_id);
          });
        }
      } catch (err) {
        console.error('Failed to load applications', err);
      } finally {
        setLoading(false);
      }
    }
    load();
    return () => (mounted = false);
  }, [token]);

  async function loadPostTitle(postId) {
    try {
      const resp = await fetchWithAuth(`/api/post/${postId}`, { method: 'GET' }, token);
      if (resp.ok) {
        setPosts(prev => ({ ...prev, [postId]: resp.data }));
      }
    } catch (err) {
      console.error('Failed to load post title for', postId, err);
    }
  }

  async function deleteApplication(id) {
    if (!confirm('Delete this application?')) return;
    try {
      const resp = await fetchWithAuth('/api/application/delete-application', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
      }, token);
      if (resp.ok) {
        setApplications(prev => prev.filter(a => a.id !== id));
        alert('Application deleted');
      } else {
        alert('Delete failed: ' + JSON.stringify(resp.data));
      }
    } catch (err) {
      alert('Error: ' + err.message);
    }
  }

  async function refreshApplications() {
    try {
      const resp = await fetchWithAuth('/api/application/me/get-application', { method: 'GET' }, token);
      if (resp.ok && Array.isArray(resp.data)) setApplications(resp.data);
    } catch (err) { console.error(err); }
  }

  return (
    <section className="applications-section">
      <h3>Your applications</h3>
      {loading && <div>Loading...</div>}
      {!loading && applications.length === 0 && <div>Không có đơn ứng tuyển</div>}

      {applications.map(a => (
        <div key={a.id} className="application-item">
          <div><strong>Post:</strong> {posts[a.post_id]?.title || 'Loading...'}</div>
          <div><strong>Status:</strong> {a.application_status}</div>
          <div><strong>Applied:</strong> {a.applied_at ? new Date(a.applied_at).toLocaleString() : ''}</div>
          <div className="app-actions">
            <button className="btn btn-danger" onClick={() => deleteApplication(a.id)}>Delete application</button>
          </div>

          {a.application_status === 'accepted' && (
            <div className="tutor-pay-section">
              <p>Please accept and pay the service fee to confirm this application.</p>
              <label>Service fee (VND):</label>
              <input type="number" defaultValue={50000} id={`fee-${a.id}`} readOnly />
              <button className="btn btn-primary" onClick={async ()=>{
                const feeEl = document.getElementById(`fee-${a.id}`);
                const amount = Number(feeEl ? feeEl.value : 0);
                if (!confirm(`Pay ${amount} VND to confirm?`)) return;
                try {
                  const resp = await fetchWithAuth('/api/transaction/pay-application', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ application_id: a.id, amount_money: amount })
                  }, token);
                  if (resp.ok) {
                    alert('Payment successful — application confirmed');
                    await refreshApplications();
                  } else {
                    alert('Payment failed: ' + JSON.stringify(resp.data));
                  }
                } catch (err) { alert('Error: ' + err.message); }
              }}>Accept & Pay</button>
            </div>
          )}
        </div>
      ))}
    </section>
  );
}
