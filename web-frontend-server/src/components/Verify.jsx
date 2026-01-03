import React, { useEffect, useState } from 'react';
import { useAuth } from '../auth';
import fetchWithAuth from '../api';
import './Verify.css';

export default function Verify() {
  const { token } = useAuth();
  const [tab, setTab] = useState('profile'); // 'profile' or 'certificate'
  const [statusFilter, setStatusFilter] = useState('pending');
  const [items, setItems] = useState([]);
  const [imagesMap, setImagesMap] = useState({}); // key: type_id -> [images]
  const [me, setMe] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadItems();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, statusFilter, token]);

  useEffect(() => {
    // load current user to check admin
    let mounted = true;
    async function loadMe(){
      if (!token) return;
      const resp = await fetchWithAuth('/api/auth/me/get-profile', { method: 'GET' }, token);
      if (mounted && resp.ok) setMe(resp.data);
    }
    loadMe();
    return ()=> mounted = false;
  }, [token]);

  async function loadItems() {
    setLoading(true);
    setError(null);
    try {
      const body = { status: statusFilter, skip: 0, limit: 200 };
      let resp;
      if (tab === 'profile') {
        resp = await fetchWithAuth('/api/auth/get-profiles-by-status', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }, token);
      } else {
        resp = await fetchWithAuth('/api/auth/get-certificates-by-status', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }, token);
      }
      if (!resp.ok) throw new Error(JSON.stringify(resp.data));
      setItems(resp.data || []);
      // fetch proof images for each item
      const map = {};
      for (const it of (resp.data || [])){
        try{
          const imgResp = await fetchWithAuth('/api/auth/get-proof-images-by-type', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: tab, type_id: it.id }) }, token);
          if (imgResp.ok) map[it.id] = imgResp.data || [];
          else map[it.id] = [];
        }catch(e){ map[it.id] = []; }
      }
      setImagesMap(map);
    } catch (err) {
      setError(err.message || String(err));
    } finally {
      setLoading(false);
    }
  }

  async function deleteAllProofImagesFor(parentId) {
    const images = imagesMap[parentId] || [];
    for (const img of images) {
      try {
        await fetchWithAuth('/api/auth/me/delete-proof-image', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: img.id }) }, token);
      } catch (e) {
        console.error('Failed to delete proof image:', e);
      }
    }
  }

  async function updateStatusFor(itemId, newStatus) {
    setError(null);
    try {
      if (tab === 'profile') {
        const resp = await fetchWithAuth('/api/auth/admin/update-profile-status', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ user_id: itemId, status: newStatus }) }, token);
        if (!resp.ok) throw new Error(JSON.stringify(resp.data));
      } else {
        const resp = await fetchWithAuth('/api/auth/admin/update-certificate-status', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ certificate_id: itemId, status: newStatus }) }, token);
        if (!resp.ok) throw new Error(JSON.stringify(resp.data));
      }
      // Auto-delete all proof images for this item
      await deleteAllProofImagesFor(itemId);
      await loadItems();
    } catch (err) {
      setError(err.message || String(err));
    }
  }

  return (
    <div className="verify-page">
      <h2>Verify</h2>
      <div className="verify-controls">
        <div className="tabs">
          <button className={tab==='profile'? 'tab active':'tab'} onClick={()=>setTab('profile')}>Profile</button>
          <button className={tab==='certificate'? 'tab active':'tab'} onClick={()=>setTab('certificate')}>Certificate</button>
        </div>
        <div className="filters">
          <label>Status:</label>
          <select value={statusFilter} onChange={e=>setStatusFilter(e.target.value)}>
            <option value="pending">pending</option>
            <option value="accepted">accepted</option>
            <option value="rejected">rejected</option>
          </select>
          <button className="btn" onClick={loadItems}>Refresh</button>
        </div>
      </div>

      {loading && <div>Loading...</div>}
      {error && <div className="error">Error: {error}</div>}

      <div className="verify-list">
        {items.length === 0 && !loading && <div className="empty">No items</div>}
        {items.map(item => (
          <div key={item.id} className="verify-item">
            {tab === 'profile' ? (
              <>
                <div className="item-main">
                  <div className="item-title">{item.display_name || item.email || item.id}</div>
                  <div className="item-meta">
                    {item.phone && <span>📞 {item.phone}</span>}
                    {item.gender && <span style={{marginLeft: 12}}>👤 {item.gender}</span>}
                  </div>
                  <div className="item-details" style={{marginTop: 8, fontSize: 13, color: '#666'}}>
                    {item.subjects && <div><strong>Subjects:</strong> {Array.isArray(item.subjects) ? item.subjects.join(', ') : item.subjects}</div>}
                    {item.levels && <div><strong>Levels:</strong> {Array.isArray(item.levels) ? item.levels.join(', ') : item.levels}</div>}
                    {item.address && <div><strong>Address:</strong> {item.address}</div>}
                    {item.bio && <div><strong>Bio:</strong> {item.bio}</div>}
                  </div>
                </div>
                <div className="item-actions">
                  <div className={`status-badge status-${(item.status||'').toLowerCase()}`}>{item.status}</div>
                  {/* thumbnails */}
                  <div style={{display:'flex', gap:8, marginLeft:8}}>
                    {(imagesMap[item.id] || []).map(img=> (
                      <div key={img.id} style={{width:48,height:36,overflow:'hidden',borderRadius:6,cursor:'pointer'}} onClick={()=>setPreview(img.image)}>
                        <img src={img.image} alt="proof" style={{width:'100%',height:'100%',objectFit:'cover'}} />
                      </div>
                    ))}
                  </div>
                  <button className="btn btn-accept" onClick={()=>updateStatusFor(item.id, 'accepted')}>Accept</button>
                  <button className="btn btn-reject" onClick={()=>updateStatusFor(item.id, 'rejected')}>Reject</button>
                </div>
              </>
            ) : (
              <>
                <div className="item-main">
                  <div className="item-title">{item.certificate_type || item.filename || item.id}</div>
                  <div className="item-meta">User: {item.user_id || ''}</div>
                  <div>
                    {item.description && <div><strong>Description:</strong> {item.description}</div>}
                    {item.filename && <div><strong>Filename:</strong> {item.filename}</div>}
                    {item.url && <div><strong>URL:</strong> <a href={item.url} target="_blank" rel="noopener noreferrer">{item.url}</a></div>}
                    </div>
                </div>
                <div className="item-actions">
                  <div className={`status-badge status-${(item.status||'').toLowerCase()}`}>{item.status}</div>
                  {/* thumbnails */}
                  <div style={{display:'flex', gap:8, marginLeft:8}}>
                    {(imagesMap[item.id] || []).map(img=> (
                      <div key={img.id} style={{width:48,height:36,overflow:'hidden',borderRadius:6,cursor:'pointer'}} onClick={()=>setPreview(img.image)}>
                        <img src={img.image} alt="proof" style={{width:'100%',height:'100%',objectFit:'cover'}} />
                      </div>
                    ))}
                  </div>
                  <button className="btn btn-accept" onClick={()=>updateStatusFor(item.id, 'accepted')}>Accept</button>
                  <button className="btn btn-reject" onClick={()=>updateStatusFor(item.id, 'rejected')}>Reject</button>
                </div>
              </>
            )}
          </div>
        ))}
      </div>
      {/* preview modal */}
      {preview && (
        <div className="cert-modal-overlay" onClick={()=>setPreview(null)}>
          <div className="cert-modal" onClick={e=>e.stopPropagation()} style={{maxWidth:800}}>
            <img src={preview} alt="preview" style={{width:'100%'}} />
            <div style={{marginTop:8, textAlign:'right'}}><button className="btn" onClick={()=>setPreview(null)}>Close</button></div>
          </div>
        </div>
      )}
    </div>
  );
}
