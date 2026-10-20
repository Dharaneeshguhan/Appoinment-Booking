/**
 * Centralized API service for communicating with the FastAPI backend.
 * Automatically injects JWT Bearer tokens and handles responses.
 * Java Full Stack comparison: Similar to an Angular HttpInterceptor or Spring RestClient with Bearer token authentication.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = localStorage.getItem("auth_token");

  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, { ...options, headers });
    
    // 204 No Content
    if (response.status === 204) {
      return null;
    }

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      let errorMessage = "An unexpected error occurred.";
      if (data && data.detail) {
        if (typeof data.detail === "string") {
          errorMessage = data.detail;
        } else if (Array.isArray(data.detail)) {
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
  // --- Auth APIs ---
  signup: (email, password, fullName) => {
    return request("/auth/signup", {
      method: "POST",
      body: JSON.stringify({
        email,
        password,
        full_name: fullName,
      }),
    });
  },

  login: (email, password) => {
    return request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  getMe: () => {
    return request("/auth/me");
  },

  // --- Slot APIs ---
  getAvailableSlots: (date = null) => {
    let endpoint = "/slots?available_only=true";
    if (date) {
      endpoint += `&date=${encodeURIComponent(date)}`;
    }
    return request(endpoint);
  },

  getAllSlots: (date = null) => {
    let endpoint = "/slots?available_only=false";
    if (date) {
      endpoint += `&date=${encodeURIComponent(date)}`;
    }
    return request(endpoint);
  },

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

  deleteSlot: (slotId) => {
    return request(`/slots/${slotId}`, {
      method: "DELETE",
    });
  },

  // --- Booking APIs ---
  bookSlot: (slotId, customerName, notes = "") => {
    return request(`/slots/${slotId}/book`, {
      method: "POST",
      body: JSON.stringify({
        customer_name: customerName,
        notes: notes || null,
      }),
    });
  },

  // Patient's own bookings
  getMyBookings: () => {
    return request("/my-bookings");
  },

  // Patient cancelling their own appointment
  cancelMyBooking: (bookingId) => {
    return request(`/my-bookings/${bookingId}/cancel`, {
      method: "POST",
    });
  },

  // --- Doctor & Admin APIs ---
  getDoctorSchedule: () => {
    return request("/doctor/schedule");
  },

  updateBookingStatus: (bookingId, status) => {
    return request(`/bookings/${bookingId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
  },

  getAllBookings: () => {
    return request("/bookings");
  },

  // --- Administrator APIs ---
  getAdminUsers: () => {
    return request("/admin/users");
  },

  toggleUserStatus: (userId, isActive) => {
    return request(`/admin/users/${userId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: isActive }),
    });
  },

  createAdminUser: (email, fullName, password, role) => {
    return request("/admin/users", {
      method: "POST",
      body: JSON.stringify({
        email,
        full_name: fullName,
        password,
        role,
      }),
    });
  },
};
