import React from "react";
import { useAuth } from "../context/AuthContext";

export default function Header({ onOpenAuth }) {
  const { user, logout } = useAuth();

  const getRoleBadgeStyle = (role) => {
    switch (role) {
      case "DOCTOR":
        return { background: "#e0e7ff", color: "#3730a3" };
      case "ADMIN":
        return { background: "#fef3c7", color: "#92400e" };
      default:
        return { background: "#dcfce7", color: "#166534" };
    }
  };

  return (
    <header className="navbar">
      <div className="brand">
        <div className="brand-icon">🩺</div>
        <div>
          <h1>Clinic Appointments</h1>
          <div style={{ fontSize: "0.75rem", color: "var(--gray-600)" }}>
            Dr. Sarah Mitchell Practice
          </div>
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        {user ? (
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: "0.9rem", fontWeight: 600 }}>{user.full_name}</div>
              <span className="badge" style={getRoleBadgeStyle(user.role)}>
                {user.role}
              </span>
            </div>
            <button
              className="btn-secondary"
              style={{ fontSize: "0.85rem", padding: "0.4rem 0.75rem" }}
              onClick={logout}
            >
              Sign Out
            </button>
          </div>
        ) : (
          <button
            className="btn-primary"
            style={{ width: "auto", fontSize: "0.9rem", padding: "0.5rem 1rem" }}
            onClick={onOpenAuth}
          >
            Sign In / Register
          </button>
        )}
      </div>
    </header>
  );
}
