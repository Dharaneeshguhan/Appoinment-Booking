import React from "react";

/**
 * Top navigation header with tab controls.
 * Java analogy: Equivalent to a Thymeleaf / JSP navigation header or Spring MVC View navigation component.
 */
export default function Header({ activeTab, setActiveTab }) {
  return (
    <header className="navbar">
      <div className="brand">
        <div className="brand-icon">📅</div>
        <div>
          <h1>Appointment Booker</h1>
        </div>
      </div>
      <nav className="nav-tabs">
        <button
          className={`tab-btn ${activeTab === "slots" ? "active" : ""}`}
          onClick={() => setActiveTab("slots")}
        >
          Available Slots
        </button>
        <button
          className={`tab-btn ${activeTab === "bookings" ? "active" : ""}`}
          onClick={() => setActiveTab("bookings")}
        >
          Confirmed Bookings
        </button>
        <button
          className={`tab-btn ${activeTab === "create" ? "active" : ""}`}
          onClick={() => setActiveTab("create")}
        >
          + Add Slot
        </button>
      </nav>
    </header>
  );
}
