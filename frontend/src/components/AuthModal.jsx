import React, { useState } from "react";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";

export default function AuthModal({ onClose, onSuccess }) {
  const { login } = useAuth();
  const [isSignup, setIsSignup] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg("");
    setIsSubmitting(true);

    try {
      let res;
      if (isSignup) {
        if (!fullName.trim()) {
          setErrorMsg("Please enter your full name.");
          setIsSubmitting(false);
          return;
        }
        res = await api.signup(email.trim(), password, fullName.trim());
      } else {
        res = await api.login(email.trim(), password);
      }

      login(res.access_token, res.user);
      onSuccess(`Welcome, ${res.user.full_name}!`);
      onClose();
    } catch (err) {
      setErrorMsg(err.message || "Authentication failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickLogin = (quickEmail, quickPassword) => {
    setEmail(quickEmail);
    setPassword(quickPassword);
    setIsSignup(false);
    setErrorMsg("");
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{isSignup ? "Create Patient Account" : "Sign In"}</h2>
          <button className="alert-close" onClick={onClose} aria-label="Close modal">
            &times;
          </button>
        </div>

        {/* Tab switcher */}
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.25rem", borderBottom: "1px solid var(--gray-200)", paddingBottom: "0.5rem" }}>
          <button
            type="button"
            className={`tab-btn ${!isSignup ? "active" : ""}`}
            onClick={() => { setIsSignup(false); setErrorMsg(""); }}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`tab-btn ${isSignup ? "active" : ""}`}
            onClick={() => { setIsSignup(true); setErrorMsg(""); }}
          >
            New Patient Sign Up
          </button>
        </div>

        {errorMsg && (
          <div className="alert alert-danger" style={{ padding: "0.6rem 0.8rem", fontSize: "0.85rem" }}>
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {isSignup && (
            <div className="form-group">
              <label htmlFor="authFullName">Full Name *</label>
              <input
                id="authFullName"
                type="text"
                className="form-input"
                placeholder="e.g. Alice Smith"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
            </div>
          )}

          <div className="form-group">
            <label htmlFor="authEmail">Email Address *</label>
            <input
              id="authEmail"
              type="email"
              className="form-input"
              placeholder="e.g. name@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="authPassword">Password *</label>
            <input
              id="authPassword"
              type="password"
              className="form-input"
              placeholder="Minimum 6 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={isSubmitting}
            style={{ marginTop: "0.5rem" }}
          >
            {isSubmitting
              ? "Please wait..."
              : isSignup
              ? "Create Patient Account"
              : "Sign In"}
          </button>
        </form>

        {/* Demo credentials helper for quick testing */}
        {!isSignup && (
          <div style={{ marginTop: "1.5rem", paddingTop: "1rem", borderTop: "1px dashed var(--gray-200)", fontSize: "0.8rem" }}>
            <p style={{ fontWeight: 600, color: "var(--gray-600)", marginBottom: "0.5rem" }}>
              Quick Demo Logins (Click to autofill):
            </p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
              <button
                type="button"
                className="btn-secondary"
                style={{ fontSize: "0.75rem", padding: "0.3rem 0.5rem" }}
                onClick={() => handleQuickLogin("doctor@clinic.com", "Doctor@123")}
              >
                👨‍⚕️ Doctor Login
              </button>
              <button
                type="button"
                className="btn-secondary"
                style={{ fontSize: "0.75rem", padding: "0.3rem 0.5rem" }}
                onClick={() => handleQuickLogin("admin@clinic.com", "Admin@123")}
              >
                ⚙️ Admin Login
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
