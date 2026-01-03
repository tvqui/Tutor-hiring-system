// Minimal fetch helpers that attach Authorization header when available
export async function fetchWithAuth(path, options = {}, token = null) {
  const headers = options.headers ? { ...options.headers } : {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(path, { ...options, headers });
  const text = await res.text();
  try {
    return { ok: res.ok, status: res.status, data: text ? JSON.parse(text) : null };
  } catch (e) {
    return { ok: res.ok, status: res.status, data: text };
  }
}

export default fetchWithAuth;
