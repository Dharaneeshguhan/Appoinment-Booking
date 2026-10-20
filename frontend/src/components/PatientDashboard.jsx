import React, { useState, useEffect, useCallback } from "react";
import SlotList from "./SlotList";
import BookingModal from "./BookingModal";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";

export default function PatientDashboard({ onNotify }) {
  const { user } = useAuth();
  const [subTab, setSubTab] = useState("available"); // 'available' | 'my-appointments'
  const [slots, setSlots] = useState([]);
  const [myBookings, setMyBookings] = useState([]);
  const [selectedDate, setSelectedDate] = useState("");
  const [isLoadingSlots, setIsLoadingSlots] = useState(false);
  const [isLoadingBookings, setIsLoadingBookings] = useState(false);
  const [selectedSlotForBooking, setSelectedSlotForBooking] = useState(null);

  const loadSlots = useCallback(async () => {
    setIsLoadingSlots(true);
    try {
      const data = await api.getAvailableSlots(selectedDate || null);
      setSlots(data);
    } catch (err) {
      onNotify("danger", err.message || "Failed to load slots.");
    } finally {
      setIsLoadingSlots(false);
    }
  }, [selectedDate, onNotify]);

  const loadMyBookings = useCallback(async () => {
    setIsLoadingBookings(true);
    try {
      const data = await api.getMyBookings();
      setMyBookings(data);
    } catch (err) {
      onNotify("danger", err.message || "Failed to load your appointments.");
    } finally {
      setIsLoadingBookings(false);
    }
  }, [onNotify]);

  useEffect(() => {
    loadSlots();
  }, [loadSlots]);

  useEffect(() => {
    if (subTab === "my-appointments") {
      loadMyBookings();
    }
  }, [subTab, loadMyBookings]);

  const handleBookingSuccess = (bookingResult, bookedSlot) => {
    onNotify(
      "success",
      `🎉 Appointment confirmed! Reserved for ${bookedSlot.slot_date} at ${bookedSlot.start_time} - ${bookedSlot.end_time}.`
    );
    loadSlots();
    loadMyBookings();
  };

  const handleBookingError = (error) => {
    onNotify("danger", error.message);
    loadSlots();
  };

  const handleCancel = async (bookingId) => {
    if (!window.confirm("Are you sure you want to cancel this appointment? The slot will be released.")) {
      return;
    }
    try {
      await api.cancelMyBooking(bookingId);
      onNotify("success", "Appointment successfully cancelled. The time slot has been freed.");
      loadMyBookings();
      loadSlots();
    } catch (err) {
      onNotify("danger", err.message || "Failed to cancel appointment.");
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "CONFIRMED":
        return <span className="badge badge-available">CONFIRMED</span>;
      case "COMPLETED":
        return <span className="badge" style={{ background: "#e0e7ff", color: "#3730a3" }}>COMPLETED</span>;
      case "CANCELLED":
        return <span className="badge badge-booked">CANCELLED</span>;
      default:
        return <span className="badge">{status}</span>;
    }
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
        <div>
          <h2 style={{ fontSize: "1.4rem", fontWeight: 700 }}>Patient Dashboard</h2>
          <p style={{ fontSize: "0.9rem", color: "var(--gray-600)" }}>
            Welcome back, <strong>{user?.full_name}</strong>. Manage your appointments and schedule new visits.
          </p>
        </div>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button
            className={`tab-btn ${subTab === "available" ? "active" : ""}`}
            onClick={() => setSubTab("available")}
          >
            📅 Browse Free Slots
          </button>
          <button
            className={`tab-btn ${subTab === "my-appointments" ? "active" : ""}`}
            onClick={() => setSubTab("my-appointments")}
          >
            📋 My Appointments ({myBookings.length})
          </button>
        </div>
      </div>

      {subTab === "available" && (
        <SlotList
          slots={slots}
          selectedDate={selectedDate}
          setSelectedDate={setSelectedDate}
          isLoading={isLoadingSlots}
          onRefresh={loadSlots}
          onSelectSlot={(slot) => setSelectedSlotForBooking(slot)}
        />
      )}

      {subTab === "my-appointments" && (
        <div>
          <div className="filter-bar">
            <div>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 700 }}>My Appointments</h3>
              <p style={{ fontSize: "0.85rem", color: "var(--gray-600)" }}>
                Your personal consultation history.
              </p>
            </div>
            <button className="btn-secondary btn-refresh" onClick={loadMyBookings} disabled={isLoadingBookings}>
              <span>🔄</span> {isLoadingBookings ? "Refreshing..." : "Refresh"}
            </button>
          </div>

          {isLoadingBookings ? (
            <div className="state-box"><p>Loading your appointments...</p></div>
          ) : myBookings.length === 0 ? (
            <div className="state-box">
              <h3>No Appointments Booked</h3>
              <p>You currently have no scheduled appointments. Switch to "Browse Free Slots" to book one.</p>
            </div>
          ) : (
            <div className="bookings-table-container">
              <table className="bookings-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Status</th>
                    <th>Notes</th>
                    <th>Booked At</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {myBookings.map((b) => (
                    <tr key={b.id}>
                      <td style={{ fontWeight: 600 }}>{b.slot?.slot_date}</td>
                      <td>{b.slot?.start_time} - {b.slot?.end_time}</td>
                      <td>{getStatusBadge(b.status)}</td>
                      <td style={{ color: "var(--gray-600)" }}>{b.notes || <em style={{ opacity: 0.6 }}>None</em>}</td>
                      <td style={{ fontSize: "0.8rem", color: "var(--gray-600)" }}>{b.booked_at}</td>
                      <td>
                        {b.status === "CONFIRMED" ? (
                          <button
                            className="btn-secondary"
                            style={{ color: "var(--danger)", borderColor: "#fecaca", padding: "0.3rem 0.6rem", fontSize: "0.8rem" }}
                            onClick={() => handleCancel(b.id)}
                          >
                            Cancel
                          </button>
                        ) : (
                          <span style={{ fontSize: "0.8rem", color: "var(--gray-600)" }}>—</span>
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

      {selectedSlotForBooking && (
        <BookingModal
          slot={selectedSlotForBooking}
          onClose={() => setSelectedSlotForBooking(null)}
          onBookingSuccess={handleBookingSuccess}
          onBookingError={handleBookingError}
        />
      )}
    </div>
  );
}
