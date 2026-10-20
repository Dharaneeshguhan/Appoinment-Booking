import React from "react";

/**
 * Renders the grid of available slots and the date filter toolbar.
 * Java analogy: Equivalent to a Data Table / Card Grid view in an admin console or client portal.
 */
export default function SlotList({
  slots,
  selectedDate,
  setSelectedDate,
  isLoading,
  onRefresh,
  onSelectSlot,
}) {
  return (
    <div>
      <div className="filter-bar">
        <div className="filter-group">
          <label htmlFor="slotDateFilter">Filter by Date:</label>
          <input
            id="slotDateFilter"
            type="date"
            className="date-input"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
          />
          {selectedDate && (
            <button
              className="btn-secondary"
              onClick={() => setSelectedDate("")}
            >
              Clear Filter
            </button>
          )}
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
          <p>Loading available slots...</p>
        </div>
      ) : slots.length === 0 ? (
        <div className="state-box">
          <h3>No Available Slots Found</h3>
          <p>
            {selectedDate
              ? `There are no free appointment slots on ${selectedDate}. Try selecting another date or check back later.`
              : "All slots are currently booked or none have been scheduled yet."}
          </p>
        </div>
      ) : (
        <div className="slots-grid">
          {slots.map((slot) => (
            <div key={slot.id} className="slot-card">
              <div>
                <div className="slot-header">
                  <div className="slot-date">📅 {slot.slot_date}</div>
                  <span className="badge badge-available">Available</span>
                </div>
                <div className="slot-time">
                  <span>⏰</span> {slot.start_time} - {slot.end_time}
                </div>
              </div>
              <button
                className="btn-primary"
                onClick={() => onSelectSlot(slot)}
              >
                Book Appointment
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
