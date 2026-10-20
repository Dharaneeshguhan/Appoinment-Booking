import React, { useState, useEffect, useCallback } from "react";
import CreateSlot from "./CreateSlot";
import { api } from "../api";

export default function DoctorDashboard({ onNotify }) {
  const [subTab, setSubTab] = useState("schedule"); // 'schedule' | 'slots'
  const [schedule, setSchedule] = useState([]);
  const [allSlots, setAllSlots] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const loadSchedule = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await api.getDoctorSchedule();
      setSchedule(data);
    } catch (err) {
      onNotify("danger", err.message || "Failed to load schedule.");
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
    if (subTab === "schedule") {
      loadSchedule();
    } else {
      loadSlots();
    }
  }, [subTab, loadSchedule, loadSlots]);

  const handleStatusChange = async (bookingId, newStatus) => {
    try {
      await api.updateBookingStatus(bookingId, newStatus);
      onNotify("success", `Appointment #${bookingId} marked as ${newStatus}.`);
      loadSchedule();
    } catch (err) {
      onNotify("danger", err.message || "Failed to update appointment status.");
    }
  };

  const handleDeleteSlot = async (slotId) => {
    if (!window.confirm("Are you sure you want to delete this unbooked slot?")) {
      return;
    }
    try {
      await api.deleteSlot(slotId);
      onNotify("success", `Slot #${slotId} removed from schedule.`);
      loadSlots();
    } catch (err) {
      onNotify("danger", err.message || "Failed to delete slot.");
    }
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
        <div>
          <h2 style={{ fontSize: "1.4rem", fontWeight: 700 }}>Doctor Portal</h2>
          <p style={{ fontSize: "0.9rem", color: "var(--gray-600)" }}>
            Review your patient appointments and manage consultation schedules.
          </p>
        </div>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button
            className={`tab-btn ${subTab === "schedule" ? "active" : ""}`}
            onClick={() => setSubTab("schedule")}
          >
            👨‍⚕️ Patient Schedule ({schedule.length})
          </button>
          <button
            className={`tab-btn ${subTab === "slots" ? "active" : ""}`}
            onClick={() => setSubTab("slots")}
          >
            ⏰ Manage Schedule Slots
          </button>
        </div>
      </div>

      {subTab === "schedule" && (
        <div>
          <div className="filter-bar">
            <div>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 700 }}>Upcoming & Past Consultations</h3>
              <p style={{ fontSize: "0.85rem", color: "var(--gray-600)" }}>
                Click action buttons to update patient appointment status.
              </p>
            </div>
            <button className="btn-secondary btn-refresh" onClick={loadSchedule} disabled={isLoading}>
              <span>🔄</span> {isLoading ? "Refreshing..." : "Refresh"}
            </button>
          </div>

          {isLoading ? (
            <div className="state-box"><p>Loading schedule...</p></div>
          ) : schedule.length === 0 ? (
            <div className="state-box">
              <h3>No Appointments Scheduled</h3>
              <p>No patients have booked appointments yet.</p>
            </div>
          ) : (
            <div className="bookings-table-container">
              <table className="bookings-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Patient Name</th>
                    <th>Notes</th>
                    <th>Current Status</th>
                    <th>Update Status</th>
                  </tr>
                </thead>
                <tbody>
                  {schedule.map((b) => (
                    <tr key={b.id}>
                      <td style={{ fontWeight: 600 }}>{b.slot?.slot_date}</td>
                      <td>{b.slot?.start_time} - {b.slot?.end_time}</td>
                      <td style={{ fontWeight: 600, color: "var(--gray-900)" }}>{b.customer_name}</td>
                      <td style={{ color: "var(--gray-600)" }}>{b.notes || <em style={{ opacity: 0.6 }}>None</em>}</td>
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
                      <td>
                        <div style={{ display: "flex", gap: "0.3rem" }}>
                          {b.status !== "COMPLETED" && (
                            <button
                              className="btn-secondary"
                              style={{ fontSize: "0.75rem", padding: "0.25rem 0.5rem", color: "var(--primary)" }}
                              onClick={() => handleStatusChange(b.id, "COMPLETED")}
                            >
                              ✓ Complete
                            </button>
                          )}
                          {b.status !== "CANCELLED" && (
                            <button
                              className="btn-secondary"
                              style={{ fontSize: "0.75rem", padding: "0.25rem 0.5rem", color: "var(--danger)" }}
                              onClick={() => handleStatusChange(b.id, "CANCELLED")}
                            >
                              ✕ Cancel
                            </button>
                          )}
                          {b.status !== "CONFIRMED" && (
                            <button
                              className="btn-secondary"
                              style={{ fontSize: "0.75rem", padding: "0.25rem 0.5rem" }}
                              onClick={() => handleStatusChange(b.id, "CONFIRMED")}
                            >
                              Confirm
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {subTab === "slots" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", alignItems: "start" }}>
          <div>
            <CreateSlot
              onSlotCreated={(newSlot) => {
                onNotify("success", `New slot created on ${newSlot.slot_date} at ${newSlot.start_time} - ${newSlot.end_time}.`);
                loadSlots();
              }}
              onError={(err) => onNotify("danger", err.message || "Failed to create slot.")}
            />
          </div>

          <div>
            <div className="filter-bar" style={{ display: "block" }}>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "0.5rem" }}>
                All Practice Slots ({allSlots.length})
              </h3>
              <p style={{ fontSize: "0.85rem", color: "var(--gray-600)", marginBottom: "1rem" }}>
                Unbooked slots can be removed from schedule.
              </p>

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
        </div>
      )}
    </div>
  );
}
