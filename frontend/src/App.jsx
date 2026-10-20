import React, { useState, useEffect, useCallback } from "react";
import Header from "./components/Header";
import SlotList from "./components/SlotList";
import BookingsList from "./components/BookingsList";
import CreateSlot from "./components/CreateSlot";
import BookingModal from "./components/BookingModal";
import { api } from "./api";
import "./App.css";

/**
 * Root Application Component.
 * Java Full Stack comparison:
 * Functions like the main Single Page Application container (e.g. Angular's AppComponent or a React router view).
 * Coordinates state, triggers API calls via services, and manages active views.
 */
export default function App() {
  const [activeTab, setActiveTab] = useState("slots"); // 'slots' | 'bookings' | 'create'
  const [slots, setSlots] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [selectedDate, setSelectedDate] = useState("");
  const [isLoadingSlots, setIsLoadingSlots] = useState(false);
  const [isLoadingBookings, setIsLoadingBookings] = useState(false);
  const [alert, setAlert] = useState(null); // { type: 'success' | 'danger', message: string }
  const [selectedSlotForBooking, setSelectedSlotForBooking] = useState(null);

  // Fetch available slots from backend
  const loadAvailableSlots = useCallback(async () => {
    setIsLoadingSlots(true);
    try {
      const data = await api.getAvailableSlots(selectedDate || null);
      setSlots(data);
    } catch (err) {
      setAlert({
        type: "danger",
        message: err.message || "Failed to load appointment slots.",
      });
    } finally {
      setIsLoadingSlots(false);
    }
  }, [selectedDate]);

  // Fetch confirmed bookings from backend
  const loadBookings = useCallback(async () => {
    setIsLoadingBookings(true);
    try {
      const data = await api.getBookings();
      setBookings(data);
    } catch (err) {
      setAlert({
        type: "danger",
        message: err.message || "Failed to load bookings.",
      });
    } finally {
      setIsLoadingBookings(false);
    }
  }, []);

  // Initial load & when date filter changes
  useEffect(() => {
    loadAvailableSlots();
  }, [loadAvailableSlots]);

  // Load bookings when switching to bookings tab
  useEffect(() => {
    if (activeTab === "bookings") {
      loadBookings();
    }
  }, [activeTab, loadBookings]);

  // Handle successful booking
  const handleBookingSuccess = (bookingResult, bookedSlot) => {
    setAlert({
      type: "success",
      message: `🎉 Booking confirmed! Appointment for "${bookingResult.customer_name}" on ${bookedSlot.slot_date} at ${bookedSlot.start_time} - ${bookedSlot.end_time} is reserved.`,
    });
    // Immediately refresh the slots so the booked one disappears
    loadAvailableSlots();
    // Also refresh the bookings list in the background
    loadBookings();
  };

  // Handle booking error (e.g. 409 Conflict)
  const handleBookingError = (error) => {
    let msg = error.message;
    if (error.status === 409) {
      msg = `⚠️ Double-booking prevented: ${error.message} The available slot list has been refreshed.`;
    }
    setAlert({
      type: "danger",
      message: msg,
    });
    // Refresh slot list to update state if someone else booked it
    loadAvailableSlots();
  };

  // Handle slot creation by staff
  const handleSlotCreated = (newSlot) => {
    setAlert({
      type: "success",
      message: `Slot successfully added for ${newSlot.slot_date} at ${newSlot.start_time} - ${newSlot.end_time}.`,
    });
    setActiveTab("slots");
    loadAvailableSlots();
  };

  return (
    <div className="app-container">
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="main-content">
        {/* Feedback Alert Banner */}
        {alert && (
          <div className={`alert alert-${alert.type}`} role="alert">
            <span>{alert.message}</span>
            <button
              className="alert-close"
              onClick={() => setAlert(null)}
              aria-label="Dismiss alert"
            >
              &times;
            </button>
          </div>
        )}

        {/* Tab 1: Available Slots */}
        {activeTab === "slots" && (
          <SlotList
            slots={slots}
            selectedDate={selectedDate}
            setSelectedDate={setSelectedDate}
            isLoading={isLoadingSlots}
            onRefresh={loadAvailableSlots}
            onSelectSlot={(slot) => setSelectedSlotForBooking(slot)}
          />
        )}

        {/* Tab 2: Confirmed Bookings */}
        {activeTab === "bookings" && (
          <BookingsList
            bookings={bookings}
            isLoading={isLoadingBookings}
            onRefresh={loadBookings}
          />
        )}

        {/* Tab 3: Create Slot (Staff) */}
        {activeTab === "create" && (
          <CreateSlot
            onSlotCreated={handleSlotCreated}
            onError={(err) =>
              setAlert({
                type: "danger",
                message: err.message || "Failed to create slot.",
              })
            }
          />
        )}
      </main>

      {/* Booking Modal */}
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
