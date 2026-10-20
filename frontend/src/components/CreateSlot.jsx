import React, { useState } from "react";
import { api } from "../api";

/**
 * Form allowing staff to add new appointment slots.
 * Java analogy: Equivalent to an Admin form submitting a new Slot entity to a Spring `@PostMapping("/slots")`.
 */
export default function CreateSlot({ onSlotCreated, onError }) {
  const [slotDate, setSlotDate] = useState("");
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("09:30");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!slotDate) {
      setFormError("Please select a valid date.");
      return;
    }
    if (!startTime || !endTime) {
      setFormError("Please provide both start and end times.");
      return;
    }
    if (endTime <= startTime) {
      setFormError("End time must be later than start time.");
      return;
    }

    setFormError("");
    setIsSubmitting(true);

    try {
      const createdSlot = await api.createSlot(slotDate, startTime, endTime);
      onSlotCreated(createdSlot);
      // Reset times to next default
      setStartTime("10:00");
      setEndTime("10:30");
    } catch (err) {
      onError(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: "560px", margin: "0 auto" }}>
      <div className="filter-bar" style={{ display: "block" }}>
        <h2 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "0.5rem" }}>
          Create New Appointment Slot
        </h2>
        <p style={{ fontSize: "0.85rem", color: "var(--gray-600)", marginBottom: "1.5rem" }}>
          Add available time slots for customers to book.
        </p>

        {formError && (
          <div className="alert alert-danger" style={{ marginBottom: "1rem" }}>
            <span>{formError}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="slotDate">
              Date <span style={{ color: "var(--danger)" }}>*</span>
            </label>
            <input
              id="slotDate"
              type="date"
              className="form-input"
              value={slotDate}
              onChange={(e) => setSlotDate(e.target.value)}
              required
            />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            <div className="form-group">
              <label htmlFor="startTime">
                Start Time (24h) <span style={{ color: "var(--danger)" }}>*</span>
              </label>
              <input
                id="startTime"
                type="time"
                className="form-input"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="endTime">
                End Time (24h) <span style={{ color: "var(--danger)" }}>*</span>
              </label>
              <input
                id="endTime"
                type="time"
                className="form-input"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                required
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={isSubmitting}
            style={{ marginTop: "0.5rem" }}
          >
            {isSubmitting ? "Creating..." : "Add Slot"}
          </button>
        </form>
      </div>
    </div>
  );
}
