import React, { useState } from "react";
import { api } from "../api";

/**
 * Modal dialog for capturing customer name and booking an appointment slot.
 * Java analogy: Equivalent to a modal dialog form submitting a DTO to a Spring POST endpoint.
 */
export default function BookingModal({ slot, onClose, onBookingSuccess, onBookingError }) {
  const [customerName, setCustomerName] = useState("");
  const [notes, setNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationError, setValidationError] = useState("");

  if (!slot) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    const trimmed = customerName.trim();
    if (!trimmed) {
      setValidationError("Please enter your name to book this appointment.");
      return;
    }

    setValidationError("");
    setIsSubmitting(true);

    try {
      const result = await api.bookSlot(slot.id, trimmed, notes.trim());
      onBookingSuccess(result, slot);
      onClose();
    } catch (err) {
      onBookingError(err);
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Book Appointment</h2>
          <button className="alert-close" onClick={onClose} aria-label="Close modal">
            &times;
          </button>
        </div>

        <div className="modal-slot-summary">
          <div><strong>Date:</strong> {slot.slot_date}</div>
          <div><strong>Time:</strong> {slot.start_time} - {slot.end_time}</div>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="customerName">
              Customer Name <span style={{ color: "var(--danger)" }}>*</span>
            </label>
            <input
              id="customerName"
              type="text"
              className="form-input"
              placeholder="e.g. Jane Doe"
              value={customerName}
              onChange={(e) => {
                setCustomerName(e.target.value);
                if (validationError) setValidationError("");
              }}
              disabled={isSubmitting}
              autoFocus
              required
            />
            {validationError && (
              <p style={{ color: "var(--danger)", fontSize: "0.8rem", marginTop: "0.25rem" }}>
                {validationError}
              </p>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="bookingNotes">Notes (Optional)</label>
            <textarea
              id="bookingNotes"
              className="form-input"
              rows={3}
              placeholder="e.g. First visit, consultation reason..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              disabled={isSubmitting}
            />
          </div>

          <div className="modal-actions">
            <button
              type="button"
              className="btn-secondary"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              style={{ width: "auto" }}
              disabled={isSubmitting}
            >
              {isSubmitting ? "Confirming..." : "Confirm Booking"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
