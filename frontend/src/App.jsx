import React, { useState, useEffect, useCallback } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Header from "./components/Header";
import AuthModal from "./components/AuthModal";
import PatientDashboard from "./components/PatientDashboard";
import DoctorDashboard from "./components/DoctorDashboard";
import AdminDashboard from "./components/AdminDashboard";
import SlotList from "./components/SlotList";
import BookingModal from "./components/BookingModal";
import { api } from "./api";
import "./App.css";

function MainContent() {
  const { user } = useAuth();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [alert, setAlert] = useState(null);

  // Guest view state
  const [slots, setSlots] = useState([]);
  const [selectedDate, setSelectedDate] = useState("");
  const [isLoadingSlots, setIsLoadingSlots] = useState(false);
  const [selectedSlotForBooking, setSelectedSlotForBooking] = useState(null);

  const notify = useCallback((type, message) => {
    setAlert({ type, message });
  }, []);

  const loadSlots = useCallback(async () => {
    setIsLoadingSlots(true);
    try {
      const data = await api.getAvailableSlots(selectedDate || null);
      setSlots(data);
    } catch (err) {
      notify("danger", err.message || "Failed to load slots.");
    } finally {
      setIsLoadingSlots(false);
    }
  }, [selectedDate, notify]);

  useEffect(() => {
    if (!user) {
      loadSlots();
    }
  }, [user, loadSlots]);

  const handleGuestSelectSlot = (slot) => {
    // If guest clicks Book Appointment, open auth modal so they can sign up/in
    setShowAuthModal(true);
    notify("success", "Please sign in or create a free patient account to book an appointment.");
  };

  return (
    <div className="app-container">
      <Header onOpenAuth={() => setShowAuthModal(true)} />

      <main className="main-content">
        {alert && (
          <div className={`alert alert-${alert.type}`} role="alert">
            <span>{alert.message}</span>
            <button className="alert-close" onClick={() => setAlert(null)} aria-label="Dismiss alert">
              &times;
            </button>
          </div>
        )}

        {/* Dynamic View Based on User Role */}
        {user?.role === "PATIENT" && (
          <PatientDashboard onNotify={notify} />
        )}

        {user?.role === "DOCTOR" && (
          <DoctorDashboard onNotify={notify} />
        )}

        {user?.role === "ADMIN" && (
          <AdminDashboard onNotify={notify} />
        )}

        {/* Public Guest View (Not Logged In) */}
        {!user && (
          <div>
            <div
              style={{
                background: "linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)",
                color: "white",
                padding: "2.5rem",
                borderRadius: "var(--radius-lg)",
                marginBottom: "2rem",
                boxShadow: "var(--shadow-md)"
              }}
            >
              <h2 style={{ fontSize: "1.75rem", fontWeight: 800, marginBottom: "0.5rem" }}>
                Welcome to Dr. Sarah Mitchell's Practice
              </h2>
              <p style={{ opacity: 0.9, maxWidth: "600px", fontSize: "1rem", lineHeight: 1.6 }}>
                Book your medical consultation easily online. Sign in with your patient account or browse available appointment times below.
              </p>
              <div style={{ marginTop: "1.25rem", display: "flex", gap: "0.75rem" }}>
                <button
                  className="btn-primary"
                  style={{ background: "white", color: "var(--primary)", width: "auto", fontWeight: 700 }}
                  onClick={() => setShowAuthModal(true)}
                >
                  Sign In / Patient Register
                </button>
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
              <h3 style={{ fontSize: "1.2rem", fontWeight: 700 }}>Available Appointment Slots</h3>
              <p style={{ fontSize: "0.85rem", color: "var(--gray-600)" }}>
                Select a slot to reserve your consultation.
              </p>
            </div>

            <SlotList
              slots={slots}
              selectedDate={selectedDate}
              setSelectedDate={setSelectedDate}
              isLoading={isLoadingSlots}
              onRefresh={loadSlots}
              onSelectSlot={handleGuestSelectSlot}
            />
          </div>
        )}
      </main>

      {/* Auth Modal (Login / Signup) */}
      {showAuthModal && (
        <AuthModal
          onClose={() => setShowAuthModal(false)}
          onSuccess={(msg) => notify("success", msg)}
        />
      )}
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <MainContent />
    </AuthProvider>
  );
}
