import React from "react";

/**
 * Table view displaying all confirmed bookings stored persistently in SQLite.
 * Java analogy: Equivalent to an Admin/Staff management table view backed by a Spring Repository findAll() method.
 */
export default function BookingsList({ bookings, isLoading, onRefresh }) {
  return (
    <div>
      <div className="filter-bar">
        <div>
          <h2 style={{ fontSize: "1.1rem", fontWeight: 700 }}>
            Confirmed Bookings ({bookings.length})
          </h2>
          <p style={{ fontSize: "0.85rem", color: "var(--gray-600)" }}>
            Stored persistently in the SQLite database.
          </p>
        </div>
        <div>
          <button
            className="btn-secondary btn-refresh"
            onClick={onRefresh}
            disabled={isLoading}
          >
            <span>🔄</span> {isLoading ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="state-box">
          <p>Loading confirmed bookings...</p>
        </div>
      ) : bookings.length === 0 ? (
        <div className="state-box">
          <h3>No Bookings Yet</h3>
          <p>When customers reserve slots, they will appear here persistently.</p>
        </div>
      ) : (
        <div className="bookings-table-container">
          <table className="bookings-table">
            <thead>
              <tr>
                <th>Booking ID</th>
                <th>Customer Name</th>
                <th>Appointment Date</th>
                <th>Time Window</th>
                <th>Notes</th>
                <th>Booked At (UTC)</th>
              </tr>
            </thead>
            <tbody>
              {bookings.map((b) => (
                <tr key={b.id}>
                  <td><strong>#{b.id}</strong></td>
                  <td style={{ fontWeight: 600, color: "var(--gray-900)" }}>
                    {b.customer_name}
                  </td>
                  <td>{b.slot ? b.slot.slot_date : "—"}</td>
                  <td>
                    {b.slot ? `${b.slot.start_time} - ${b.slot.end_time}` : "—"}
                  </td>
                  <td style={{ color: "var(--gray-600)" }}>
                    {b.notes || <em style={{ opacity: 0.6 }}>None</em>}
                  </td>
                  <td style={{ fontSize: "0.8rem", color: "var(--gray-600)" }}>
                    {b.booked_at}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
