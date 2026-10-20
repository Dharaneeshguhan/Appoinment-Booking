/**
 * Centralized API service for communicating with the FastAPI backend.
 * Java Full Stack comparison: Similar to an Angular/React HttpService or a Spring RestTemplate/WebClient wrapper.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  try {
    const response = await fetch(url, { ...options, headers });
    const data = await response.json().catch(() => null);

    if (!response.ok) {
      let errorMessage = "An unexpected error occurred.";
      if (data && data.detail) {
        if (typeof data.detail === "string") {
          errorMessage = data.detail;
        } else if (Array.isArray(data.detail)) {
          // Handle Pydantic 422 validation errors
          errorMessage = data.detail.map((err) => `${err.loc.join('.')}: ${err.msg}`).join(", ");
        }
      }
      const error = new Error(errorMessage);
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  } catch (err) {
    if (err.name === "TypeError" && err.message.includes("Failed to fetch")) {
      const connError = new Error(
        `Unable to connect to the backend API at ${API_BASE_URL}. Ensure the FastAPI server is running.`
      );
      connError.status = 503;
      throw connError;
    }
    throw err;
  }
}

export const api = {
  // Get available slots, optionally filtered by date (YYYY-MM-DD)
  getAvailableSlots: (date = null) => {
    let endpoint = "/slots?available_only=true";
    if (date) {
      endpoint += `&date=${encodeURIComponent(date)}`;
    }
    return request(endpoint);
  },

  // Get all slots (both booked and unbooked)
  getAllSlots: (date = null) => {
    let endpoint = "/slots?available_only=false";
    if (date) {
      endpoint += `&date=${encodeURIComponent(date)}`;
    }
    return request(endpoint);
  },

  // Book a specific slot
  bookSlot: (slotId, customerName, notes = "") => {
    return request(`/slots/${slotId}/book`, {
      method: "POST",
      body: JSON.stringify({
        customer_name: customerName,
        notes: notes || null,
      }),
    });
  },

  // Retrieve confirmed bookings list
  getBookings: () => {
    return request("/bookings");
  },

  // Optional: create a new slot
  createSlot: (slotDate, startTime, endTime) => {
    return request("/slots", {
      method: "POST",
      body: JSON.stringify({
        slot_date: slotDate,
        start_time: startTime,
        end_time: endTime,
      }),
    });
  },
};
