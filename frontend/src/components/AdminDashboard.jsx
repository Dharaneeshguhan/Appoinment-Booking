import React, { useState, useEffect, useCallback } from "react";
import CreateSlot from "./CreateSlot";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";

export default function AdminDashboard({ onNotify }) {
  const { user } = useAuth();
  const [subTab, setSubTab] = useState("users"); // 'users' | 'bookings' | 'slots'
  const [users, setUsers] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [allSlots, setAllSlots] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // New user form state
  const [showAddUser, setShowAddUser] = useState(false);
  const [newUserEmail, setNewUserEmail] = useState("");
  const [newUserName, setNewUserName] = useState("");
  const [newUserPass, setNewUserPass] = useState("");
  const [newUserRole, setNewUserRole] = useState("PATIENT");
  const [isCreatingUser, setIsCreatingUser] = useState(false);

  const loadUsers = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await api.getAdminUsers();
      setUsers(data);
    } catch (err) {
      onNotify("danger", err.message || "Failed to load users.");
    } finally {
      setIsLoading(false);
    }
  }, [onNotify]);

  const loadBookings = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await api.getAllBookings();
      setBookings(data);
    } catch (err) {
      onNotify("danger", err.message || "Failed to load bookings.");
    } finally {
      setIsLoading(false);
    }
  }, [onNotify]);

  const loadSlots = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await api.getAllSlots();
      setAllSlots(data);
    } catch (err) {
      onNotify("danger", err.message || "Failed to load slots.");
    } finally {
      setIsLoading(false);
    }
  }, [onNotify]);

  useEffect(() => {
    if (subTab === "users") loadUsers();
    else if (subTab === "bookings") loadBookings();
    else if (subTab === "slots") loadSlots();
  }, [subTab, loadUsers, loadBookings, loadSlots]);

  const handleToggleStatus = async (targetUser) => {
    if (targetUser.id === user.id && targetUser.is_active) {
      onNotify("danger", "Administrators cannot deactivate their own account.");
      return;
    }
    const action = targetUser.is_active ? "deactivate" : "activate";
    if (!window.confirm(`Are you sure you want to ${action} ${targetUser.full_name}'s account?`)) {
      return;
    }

    try {
      await api.toggleUserStatus(targetUser.id, !targetUser.is_active);
      onNotify("success", `User ${targetUser.email} is now ${!targetUser.is_active ? "active" : "inactive"}.`);
      loadUsers();
    } catch (err) {
      onNotify("danger", err.message || "Failed to update user status.");
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setIsCreatingUser(true);
    try {
      await api.createAdminUser(newUserEmail.trim(), newUserName.trim(), newUserPass, newUserRole);
      onNotify("success", `User account created for ${newUserEmail} with role ${newUserRole}.`);
      setShowAddUser(false);
      setNewUserEmail("");
      setNewUserName("");
      setNewUserPass("");
      loadUsers();
    } catch (err) {
      onNotify("danger", err.message || "Failed to create user.");
    } finally {
      setIsCreatingUser(false);
    }
  };

  const handleDeleteSlot = async (slotId) => {
    if (!window.confirm("Are you sure you want to delete this unbooked slot?")) return;
    try {
      await api.deleteSlot(slotId);
      onNotify("success", `Slot #${slotId} deleted.`);
      loadSlots();
    } catch (err) {
      onNotify("danger", err.message || "Failed to delete slot.");
    }
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
        <div>
          <h2 style={{ fontSize: "1.4rem", fontWeight: 700 }}>Administrator Console</h2>
          <p style={{ fontSize: "0.9rem", color: "var(--gray-600)" }}>
            System oversight: Manage registered users, view all practice bookings, and configure schedule slots.
          </p>
        </div>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button
            className={`tab-btn ${subTab === "users" ? "active" : ""}`}
            onClick={() => setSubTab("users")}
          >
            👥 User Management ({users.length})
          </button>
          <button
            className={`tab-btn ${subTab === "bookings" ? "active" : ""}`}
            onClick={() => setSubTab("bookings")}
          >
            📋 All Bookings ({bookings.length})
          </button>
          <button
            className={`tab-btn ${subTab === "slots" ? "active" : ""}`}
            onClick={() => setSubTab("slots")}
          >
            ⏰ Manage Slots
          </button>
        </div>
      </div>

      {subTab === "users" && (
        <div>
          <div className="filter-bar">
            <div>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 700 }}>Registered Users</h3>
              <p style={{ fontSize: "0.85rem", color: "var(--gray-600)" }}>
                Patients, Doctors, and Administrators.
              </p>
            </div>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <button
                className="btn-primary"
                style={{ width: "auto", fontSize: "0.85rem", padding: "0.4rem 0.8rem" }}
                onClick={() => setShowAddUser(!showAddUser)}
              >
                {showAddUser ? "✕ Close Form" : "+ Create User"}
              </button>
              <button className="btn-secondary btn-refresh" onClick={loadUsers} disabled={isLoading}>
                <span>🔄</span> {isLoading ? "..." : "Refresh"}
              </button>
            </div>
          </div>

          {showAddUser && (
            <div className="filter-bar" style={{ display: "block", marginBottom: "1.5rem", borderLeft: "4px solid var(--primary)" }}>
              <h4 style={{ marginBottom: "1rem", fontWeight: 700 }}>Create New User Account</h4>
              <form onSubmit={handleCreateUser}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                  <div className="form-group">
                    <label>Full Name *</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="e.g. Dr. John Watson"
                      value={newUserName}
                      onChange={(e) => setNewUserName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Email Address *</label>
                    <input
                      type="email"
                      className="form-input"
                      placeholder="e.g. watson@clinic.com"
                      value={newUserEmail}
                      onChange={(e) => setNewUserEmail(e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                  <div className="form-group">
                    <label>Temporary Password *</label>
                    <input
                      type="password"
                      className="form-input"
                      placeholder="Min 6 characters"
                      value={newUserPass}
                      onChange={(e) => setNewUserPass(e.target.value)}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Assigned Role *</label>
                    <select
                      className="form-input"
                      value={newUserRole}
                      onChange={(e) => setNewUserRole(e.target.value)}
                    >
                      <option value="PATIENT">Patient</option>
                      <option value="DOCTOR">Doctor</option>
                      <option value="ADMIN">Administrator</option>
                    </select>
                  </div>
                </div>

                <button
                  type="submit"
                  className="btn-primary"
                  style={{ width: "auto" }}
                  disabled={isCreatingUser}
                >
                  {isCreatingUser ? "Saving..." : "Save User"}
                </button>
              </form>
            </div>
          )}

          {isLoading ? (
            <div className="state-box"><p>Loading users...</p></div>
          ) : (
            <div className="bookings-table-container">
              <table className="bookings-table">
                <thead>
                  <tr>
                    <th>User ID</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Account Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id}>
                      <td>#{u.id}</td>
                      <td style={{ fontWeight: 600 }}>{u.full_name}</td>
                      <td>{u.email}</td>
                      <td>
                        <span
                          className="badge"
                          style={{
                            background:
                              u.role === "ADMIN" ? "#fef3c7" :
                              u.role === "DOCTOR" ? "#e0e7ff" : "#dcfce7",
                            color:
                              u.role === "ADMIN" ? "#92400e" :
                              u.role === "DOCTOR" ? "#3730a3" : "#166534"
                          }}
                        >
                          {u.role}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${u.is_active ? "badge-available" : "badge-booked"}`}>
                          {u.is_active ? "ACTIVE" : "DISABLED"}
                        </span>
                      </td>
                      <td>
                        {u.id !== user.id && (
                          <button
                            className="btn-secondary"
                            style={{
                              fontSize: "0.75rem",
                              padding: "0.25rem 0.5rem",
                              color: u.is_active ? "var(--danger)" : "var(--success)"
                            }}
                            onClick={() => handleToggleStatus(u)}
                          >
                            {u.is_active ? "Deactivate" : "Activate"}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {subTab === "bookings" && (
        <div>
          <div className="filter-bar">
            <div>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 700 }}>Master Practice Bookings</h3>
              <p style={{ fontSize: "0.85rem", color: "var(--gray-600)" }}>
                Audit trail of all patient consultations.
              </p>
            </div>
            <button className="btn-secondary btn-refresh" onClick={loadBookings} disabled={isLoading}>
              <span>🔄</span> {isLoading ? "..." : "Refresh"}
            </button>
          </div>

          <div className="bookings-table-container">
            <table className="bookings-table">
              <thead>
                <tr>
                  <th>Booking ID</th>
                  <th>Patient Name</th>
                  <th>Date & Time</th>
                  <th>Status</th>
                  <th>Notes</th>
                  <th>Booked At</th>
                </tr>
              </thead>
              <tbody>
                {bookings.map((b) => (
                  <tr key={b.id}>
                    <td>#{b.id}</td>
                    <td style={{ fontWeight: 600 }}>{b.customer_name}</td>
                    <td>{b.slot?.slot_date} ({b.slot?.start_time} - {b.slot?.end_time})</td>
                    <td>
                      <span
                        className="badge"
                        style={{
                          background:
                            b.status === "CONFIRMED" ? "#dcfce7" :
                            b.status === "COMPLETED" ? "#e0e7ff" : "#fee2e2",
                          color:
                            b.status === "CONFIRMED" ? "#166534" :
                            b.status === "COMPLETED" ? "#3730a3" : "#991b1b"
                        }}
                      >
                        {b.status}
                      </span>
                    </td>
                    <td style={{ color: "var(--gray-600)" }}>{b.notes || <em style={{ opacity: 0.6 }}>None</em>}</td>
                    <td style={{ fontSize: "0.8rem", color: "var(--gray-600)" }}>{b.booked_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {subTab === "slots" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", alignItems: "start" }}>
          <CreateSlot
            onSlotCreated={() => {
              onNotify("success", "Slot created.");
              loadSlots();
            }}
            onError={(err) => onNotify("danger", err.message || "Failed to create slot.")}
          />

          <div className="filter-bar" style={{ display: "block" }}>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "0.5rem" }}>
              All Slots ({allSlots.length})
            </h3>
            <div style={{ maxHeight: "420px", overflowY: "auto" }}>
              {allSlots.map((s) => (
                <div
                  key={s.id}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "0.6rem 0.75rem",
                    borderBottom: "1px solid var(--gray-200)",
                    fontSize: "0.85rem"
                  }}
                >
                  <div>
                    <strong>{s.slot_date}</strong>: {s.start_time} - {s.end_time}
                    <span
                      className="badge"
                      style={{
                        marginLeft: "0.5rem",
                        fontSize: "0.7rem",
                        background: s.is_booked ? "#fee2e2" : "#dcfce7",
                        color: s.is_booked ? "#991b1b" : "#166534"
                      }}
                    >
                      {s.is_booked ? "Booked" : "Available"}
                    </span>
                  </div>

                  {!s.is_booked && (
                    <button
                      className="btn-secondary"
                      style={{ fontSize: "0.75rem", padding: "0.2rem 0.4rem", color: "var(--danger)", borderColor: "#fecaca" }}
                      onClick={() => handleDeleteSlot(s.id)}
                    >
                      Delete
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
