import { useState } from "react";
import fetchWithAuth from "../api";
import { useAuth } from "../auth";
import "./Login.css";

export default function Login() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function doLogin(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const resp = await fetchWithAuth("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (resp.ok && resp.data && resp.data.access_token) {
        const token = resp.data.access_token;
        // Fetch user profile to get role
        const profileResp = await fetchWithAuth("/api/auth/me/get-profile", {
          method: "GET",
          headers: { "Authorization": `Bearer ${token}` },
        });
        if (profileResp.ok && profileResp.data) {
          login(token, profileResp.data);
        } else {
          // Fallback: login with token even if profile fetch fails
          login(token, { role: "customer" });
        }
      } else {
        setError(resp.data?.detail || `Login failed (${resp.status})`);
      }
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h1>Tutor Finder</h1>
          <p>Find your perfect tutor or student</p>
        </div>
        
        <form onSubmit={doLogin} className="login-form">
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="login-button" disabled={loading}>
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>

        <div className="demo-users">
          <p>Demo accounts:</p>
          <ul>
            <li><strong>herta</strong> / 123456</li>
            <li><strong>bronya</strong> / 123456</li>
            <li><strong>jingyuan</strong> / 123456</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
