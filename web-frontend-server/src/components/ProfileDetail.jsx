import React, { useEffect, useState } from 'react';
import { useAuth } from '../auth';
import fetchWithAuth from '../api';
import './ProfileDetail.css';

export default function ProfileDetail() {
  const { token } = useAuth();
  const [profile, setProfile] = useState(null);
  const [applications, setApplications] = useState([]);
  const [certificates, setCertificates] = useState([]);
  const [profileProofs, setProfileProofs] = useState([]);
  const [certProofs, setCertProofs] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showVerifModal, setShowVerifModal] = useState(false);
  const [verifTarget, setVerifTarget] = useState({ type: 'profile', type_id: null });
  const [verifFiles, setVerifFiles] = useState([]);

  // local edit state for profile
  const [editProfile, setEditProfile] = useState(null);

  useEffect(() => {
    let mounted = true;
    async function loadAll() {
      setLoading(true);
      setError(null);
      try {
        const [pResp, aResp, cResp] = await Promise.all([
          fetchWithAuth('/api/auth/me/get-profile', { method: 'GET' }, token),
          fetchWithAuth('/api/application/me/get-application?skip=0&limit=100', { method: 'GET' }, token),
          fetchWithAuth('/api/auth/me/get-certificate', { method: 'GET' }, token)
        ]);

        if (!pResp.ok) throw new Error('Failed to load profile');
        if (!aResp.ok) throw new Error('Failed to load applications');
        if (!cResp.ok) {
          // no certificates yet -> empty
          if (cResp.status === 404) {
            if (mounted) setCertificates([]);
          } else throw new Error('Failed to load certificates');
        }

        if (mounted) {
          setProfile(pResp.data);
          // load profile proofs
          try{
            const imgResp = await fetchWithAuth('/api/auth/get-proof-images-by-type', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: 'profile', type_id: pResp.data.id }) }, token);
            if (imgResp.ok) setProfileProofs(imgResp.data || []);
          }catch(e){ setProfileProofs([]); }
          // set verif target for profile
          setVerifTarget({ type: 'profile', type_id: pResp.data.id });
          setEditProfile({
            phone: pResp.data.phone || '',
            display_name: pResp.data.display_name || '',
            subjects: (pResp.data.subjects || []).join(', '),
            levels: (pResp.data.levels || []).join(', '),
            gender: pResp.data.gender || '',
            address: pResp.data.address || '',
            bio: pResp.data.bio || ''
          });
          setApplications(aResp.data || []);
          setCertificates(cResp.ok ? cResp.data : []);
          // load proofs for certificates
          if (cResp.ok && Array.isArray(cResp.data)){
            const map = {};
            for (const c of cResp.data){
              try{
                const r = await fetchWithAuth('/api/auth/get-proof-images-by-type', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: 'certificate', type_id: c.id }) }, token);
                map[c.id] = r.ok ? r.data || [] : [];
              }catch(e){ map[c.id] = []; }
            }
            setCertProofs(map);
          }
        }
      } catch (err) {
        if (mounted) setError(err.message || String(err));
      } finally {
        if (mounted) setLoading(false);
      }
    }
    loadAll();
    return () => (mounted = false);
  }, [token]);

  async function refreshApplications() {
    const aResp = await fetchWithAuth('/api/application/me/get-application?skip=0&limit=100', { method: 'GET' }, token);
    if (aResp.ok) setApplications(aResp.data || []);
  }

  async function refreshCertificates() {
    const cResp = await fetchWithAuth('/api/auth/me/get-certificate', { method: 'GET' }, token);
    if (cResp.ok) setCertificates(cResp.data || []);
    else if (cResp.status === 404) setCertificates([]);
  }

  // profile update
  async function saveProfile(e) {
    e.preventDefault();
    setError(null);
    try {
      const body = {
        phone: editProfile.phone || undefined,
        display_name: editProfile.display_name || undefined,
        subjects: editProfile.subjects ? editProfile.subjects.split(',').map(s=>s.trim()).filter(Boolean) : undefined,
        levels: editProfile.levels ? editProfile.levels.split(',').map(s=>s.trim()).filter(Boolean) : undefined,
        gender: editProfile.gender || undefined,
        address: editProfile.address || undefined,
        bio: editProfile.bio || undefined
      };

      const resp = await fetchWithAuth('/api/auth/me/update-profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      }, token);

      if (!resp.ok) throw new Error('Failed to update profile: ' + JSON.stringify(resp.data));
      setProfile(resp.data);
      // keep editProfile synced
      setEditProfile({
        phone: resp.data.phone || '',
        display_name: resp.data.display_name || '',
        subjects: (resp.data.subjects || []).join(', '),
        levels: (resp.data.levels || []).join(', '),
        gender: resp.data.gender || '',
        address: resp.data.address || '',
        bio: resp.data.bio || ''
      });
    } catch (err) {
      setError(err.message || String(err));
    }
  }

  // delete application
  async function deleteApplication(appId) {
    if (!confirm('Bạn có chắc muốn xóa đơn ứng tuyển này?')) return;
    const resp = await fetchWithAuth('/api/application/delete-application', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: appId })
    }, token);
    if (!resp.ok) return alert('Xóa thất bại: ' + JSON.stringify(resp.data));
    await refreshApplications();
  }

  // certificates: add, update, delete
  async function addCertificate(cert) {
    const resp = await fetchWithAuth('/api/auth/me/add-certificate', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(cert)
    }, token);
    if (!resp.ok) return alert('Add certificate failed: ' + JSON.stringify(resp.data));
    await refreshCertificates();
  }

  async function updateCertificate(cert) {
    const resp = await fetchWithAuth('/api/auth/me/update-certificate', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(cert)
    }, token);
    if (!resp.ok) return alert('Update certificate failed: ' + JSON.stringify(resp.data));
    await refreshCertificates();
  }

  async function deleteCertificate(id) {
    if (!confirm('Bạn có chắc muốn xóa chứng chỉ này?')) return;
    const resp = await fetchWithAuth('/api/auth/me/delete-certificate', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id })
    }, token);
    if (!resp.ok) return alert('Delete certificate failed: ' + JSON.stringify(resp.data));
    await refreshCertificates();
  }

  async function deleteProof(id, type, parentId){
    if (!confirm('Xóa ảnh bằng chứng?')) return;
    const resp = await fetchWithAuth('/api/auth/me/delete-proof-image', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }) }, token);
    if (!resp.ok) return alert('Delete failed: ' + JSON.stringify(resp.data));
    if (type === 'profile'){
      const imgResp = await fetchWithAuth('/api/auth/get-proof-images-by-type', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: 'profile', type_id: parentId }) }, token);
      if (imgResp.ok) setProfileProofs(imgResp.data || []);
    } else {
      const imgResp = await fetchWithAuth('/api/auth/get-proof-images-by-type', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type: 'certificate', type_id: parentId }) }, token);
      if (imgResp.ok) setCertProofs(prev=>({ ...prev, [parentId]: imgResp.data || [] }));
    }
  }

  // verification modal helpers
  function openVerificationForProfile() {
    setVerifTarget({ type: 'profile', type_id: profile.id });
    setVerifFiles([]);
    setShowVerifModal(true);
  }

  function openVerificationForCertificate(cert) {
    setVerifTarget({ type: 'certificate', type_id: cert.id });
    setVerifFiles([]);
    setShowVerifModal(true);
  }

  function onSelectFiles(e) {
    const files = Array.from(e.target.files || []);
    const readers = files.map(f => {
      return new Promise((res, rej) => {
        const r = new FileReader();
        r.onload = () => res({ name: f.name, data: r.result });
        r.onerror = rej;
        r.readAsDataURL(f);
      })
    });
    Promise.all(readers).then(arr => setVerifFiles(arr)).catch(err => console.error(err));
  }

  async function sendVerificationRequest() {
    setError(null);
    try {
      // upload proof images
      for (const f of verifFiles) {
        const body = { type: verifTarget.type, type_id: verifTarget.type_id, image: f.data };
        const resp = await fetchWithAuth('/api/auth/me/add-proof-image', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }, token);
        if (!resp.ok) throw new Error('Failed to upload proof image: ' + JSON.stringify(resp.data));
      }

      // request verification depending on type
      if (verifTarget.type === 'profile') {
        const resp = await fetchWithAuth('/api/auth/me/request-profile-verification', { method: 'POST' }, token);
        if (!resp.ok) throw new Error('Failed to request profile verification: ' + JSON.stringify(resp.data));
      } else {
        const resp = await fetchWithAuth('/api/auth/me/request-certificate-verification', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ certificate_id: verifTarget.type_id }) }, token);
        if (!resp.ok) throw new Error('Failed to request certificate verification: ' + JSON.stringify(resp.data));
      }

      setShowVerifModal(false);
      // refresh profile and certificates
      const pResp = await fetchWithAuth('/api/auth/me/get-profile', { method: 'GET' }, token);
      if (pResp.ok) setProfile(pResp.data);
      await refreshCertificates();
      alert('Verification request sent');
    } catch (err) {
      setError(err.message || String(err));
    }
  }

  if (loading) return <div className="profile-page">Loading...</div>;
  if (error) return <div className="profile-page">Error: {error}</div>;

  const profileAvg = profile && profile.avg_rating != null ? Number(profile.avg_rating) : NaN;

  return (
    <div className="profile-page">
      <h2>Personal information</h2>
      {profile && Number.isFinite(profileAvg) && (
        <div className="profile-rating">
          <span className="stars">{renderStars(profileAvg)}</span>
          <span className="rating-meta" style={{marginLeft:8}}>{profileAvg.toFixed(2)} · ({profile.rating_count || 0})</span>
        </div>
      )}
      {/* profile status badge */}
      {profile && (
        <div style={{marginTop:8}}>
          {profile.status && (
            <><strong>Status:</strong> <span className={`status-badge status-${(profile.status||'').toLowerCase()}`}>{profile.status}</span></>
          )}
          {/* Verification request button for profile (only show if not already pending) */}
          {profile.status !== 'pending' && (
            <button className="btn" style={{marginLeft:12}} onClick={openVerificationForProfile}>Verification request</button>
          )}
          {/* profile proof thumbnails */}
          <div style={{display:'flex', gap:8, marginTop:8}}>
            {profileProofs.map(pi => (
              <div key={pi.id} style={{width:96,height:72,overflow:'hidden',borderRadius:6,position:'relative'}}>
                <img src={pi.image} alt="proof" style={{width:'100%',height:'100%',objectFit:'cover'}} />
                <button className="btn" style={{position:'absolute',right:6,top:6,padding:'2px 6px'}} onClick={()=>deleteProof(pi.id,'profile', profile.id)}>Del</button>
              </div>
            ))}
          </div>
        </div>
      )}
      <form className="profile-form" onSubmit={saveProfile}>
        <label>Display name</label>
        <input value={editProfile?.display_name || ''} onChange={e=>setEditProfile({...editProfile, display_name: e.target.value})} />
        <label>Phone</label>
        <input value={editProfile?.phone || ''} onChange={e=>setEditProfile({...editProfile, phone: e.target.value})} />
        <label>Subjects</label>
        <input value={editProfile?.subjects || ''} onChange={e=>setEditProfile({...editProfile, subjects: e.target.value})} />
        <label>Levels</label>
        <input value={editProfile?.levels || ''} onChange={e=>setEditProfile({...editProfile, levels: e.target.value})} />
        <label>Gender</label>
        <input value={editProfile?.gender || ''} onChange={e=>setEditProfile({...editProfile, gender: e.target.value})} />
        <label>Address</label>
        <input value={editProfile?.address || ''} onChange={e=>setEditProfile({...editProfile, address: e.target.value})} />
        <label>Bio</label>
        <input value={editProfile?.bio || ''} onChange={e=>setEditProfile({...editProfile, bio: e.target.value})} />
        <button type="submit" className="btn btn-primary">Save information</button>
      </form>

      <section className="certificates-section">
        <h3>Certificates</h3>
        <CertificateEditorList certificates={certificates} onAdd={addCertificate} onUpdate={updateCertificate} onDelete={deleteCertificate} onRequestVerification={openVerificationForCertificate} />
      </section>

      {/* Verification modal (simple overlay) */}
      {showVerifModal && (
        <div className="cert-modal-overlay" onClick={(e)=>{ if (e.target.classList && e.target.classList.contains('cert-modal-overlay')) setShowVerifModal(false); }}>
          <div className="cert-modal" role="dialog" aria-modal="true" onClick={e=>e.stopPropagation()}>
            <h3>Upload proof images</h3>
            <div style={{marginBottom:8}}>
              <input type="file" multiple accept="image/*" onChange={onSelectFiles} />
            </div>
            <div style={{display:'flex',gap:8,flexWrap:'wrap',marginBottom:8}}>
              {verifFiles.map((f, idx) => (
                <div key={idx} style={{width:120,height:80,overflow:'hidden',border:'1px solid #eee',borderRadius:6}}>
                  <img src={f.data} alt={f.name} style={{width:'100%',height:'100%',objectFit:'cover'}} />
                </div>
              ))}
            </div>
            <div className="modal-actions">
              <button className="btn btn-cancel" onClick={()=>setShowVerifModal(false)}>Cancel</button>
              <button className="btn btn-add" onClick={sendVerificationRequest}>Send</button>
            </div>
          </div>
        </div>
      )}

      <section className="applications-section">
        <h3>Your application</h3>
        {applications.length === 0 && <div>Không có đơn ứng tuyển</div>}
        {applications.map(a => (
          <div key={a.id} className="application-item">
            <div><strong>Post:</strong> {a.post_id}</div>
            <div><strong>Status:</strong> {a.application_status}</div>
            <div><strong>Applied:</strong> {a.applied_at ? new Date(a.applied_at).toLocaleString() : ''}</div>
            <div className="app-actions">
              <button className="btn btn-danger" onClick={()=>deleteApplication(a.id)}>Delete application</button>
            </div>

            {/* If admin selected (application_status == 'accepted'), show Accept & Pay flow for tutor */}
            {a.application_status === 'accepted' && (
              <div className="tutor-pay-section">
                <p>Please accept and pay the service fee to confirm this application.</p>
                <label>Service fee (VND):</label>
                <input type="number" defaultValue={50000} id={`fee-${a.id}`} />
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

      
    </div>
  );
}

function renderStars(avg) {
  const full = Math.floor(avg);
  const half = avg - full >= 0.5 ? 1 : 0;
  const empty = 5 - full - half;
  return '★'.repeat(full) + (half ? '☆' : '') + '☆'.repeat(empty);
}

function CertificateEditorList({ certificates, onAdd, onUpdate, onDelete, onRequestVerification }) {
  const [adding, setAdding] = useState(false);
  const [newCert, setNewCert] = useState({ certificate_type: '', description: '', url: '', filename: '' });

  return (
    <div>
      {certificates.length === 0 && <div>Không có chứng chỉ</div>}
      {certificates.map(c => (
        <CertificateItem key={c.id} cert={c} onUpdate={onUpdate} onDelete={onDelete} onRequestVerification={onRequestVerification} />
      ))}
{/* add certificate */}
      <>
        <button className="btn" onClick={()=>setAdding(true)}>Add a certificate</button>

        {adding && (
          <div className="cert-modal-overlay" onClick={(e)=>{ if (e.target.classList && e.target.classList.contains('cert-modal-overlay')) setAdding(false); }}>
            <div className="cert-modal" role="dialog" aria-modal="true" onClick={e=>e.stopPropagation()}>
              <h3>Add a Certificate</h3>
              <div className="cert-add">
                <input placeholder="Type" value={newCert.certificate_type} onChange={e=>setNewCert({...newCert, certificate_type: e.target.value})} />
                <input placeholder="Description" value={newCert.description} onChange={e=>setNewCert({...newCert, description: e.target.value})} />
                <input placeholder="URL" value={newCert.url} onChange={e=>setNewCert({...newCert, url: e.target.value})} />
                <input placeholder="Filename" value={newCert.filename} onChange={e=>setNewCert({...newCert, filename: e.target.value})} />
              </div>

              <div className="modal-actions">
                <button className="btn btn-cancel" onClick={()=>setAdding(false)}>Cancel</button>
                <button className="btn btn-add" onClick={async ()=>{ await onAdd(newCert); setNewCert({certificate_type:'',description:'',url:'',filename:''}); setAdding(false); }}>Add</button>
              </div>
            </div>
          </div>
        )}
      </>
    </div>
  )
}

function CertificateItem({ cert, onUpdate, onDelete, onRequestVerification }){
  const [editing, setEditing] = useState(false);
  const [data, setData] = useState(cert);

  useEffect(()=>setData(cert), [cert]);

  if (editing) {
    return (
      <div className="cert-item editing">
        <input value={data.certificate_type} onChange={e=>setData({...data, certificate_type: e.target.value})} />
        <input value={data.description} onChange={e=>setData({...data, description: e.target.value})} />
        <input value={data.url} onChange={e=>setData({...data, url: e.target.value})} />
        <input value={data.filename} onChange={e=>setData({...data, filename: e.target.value})} />
        <button className="btn" onClick={async ()=>{ await onUpdate(data); setEditing(false); }}>Save</button>
        <button className="btn" onClick={()=>setEditing(false)}>Cancel</button>
      </div>
    )
  }

  return (
    <div className="cert-item">
      <div><strong>{cert.certificate_type}</strong> — {cert.filename || ''}</div>
      <div>{cert.description}</div>
      {cert.status && (
        <div style={{marginTop:6}}><strong>Status:</strong> <span className={`status-badge status-${(cert.status||'').toLowerCase()}`}>{cert.status}</span></div>
      )}
      {/* Verification request button for this certificate */}
      {cert && cert.status !== 'pending' && (
        <div style={{marginTop:6}}>
          <button className="btn" onClick={()=>onRequestVerification && onRequestVerification(cert)}>Verification request</button>
        </div>
      )}
      <div>{cert.url && <a href={cert.url} target="_blank" rel="noreferrer">Link</a>}</div>
      <div className="cert-actions">
        <button className="btn" onClick={()=>setEditing(true)}>Edit</button>
        <button className="btn btn-danger" onClick={()=>onDelete(cert.id)}>Delete</button>
      </div>
    </div>
  )
}
