# Intent: Appointment Slot Booker

## What to build
Build a small Appointment Slot Booker JSON API for managing appointment slots. Users can view available slots and book one slot for an appointment. The API must prevent two bookings from claiming the same slot.

## Who uses it
Clients and staff of a small appointment-based service calling a JSON API.

## Must-have behaviors
- List available appointment slots, optionally filtered by date.
- Book an available slot with the customer's name and return the booking details.
- Reject a booking if the slot does not exist or has already been booked; never allow double-booking.
- Return clear JSON responses and appropriate HTTP status codes for success and errors.

## Out of scope
- User accounts, authentication, and role-based permissions.
- Payments, email/SMS reminders, and calendar integrations.
- Recurring appointments, waitlists, and multi-time-zone scheduling.

## Decisions already made
- Stack: Python with a file-based SQLite database (or a simple in-memory store) — no Docker, no database server to install. Any cloud/Terraform is authored, not applied.
- Tests: plain pytest, run locally. Do not require Docker, testcontainers, or an external database.
- Auth: none for now (keep it simple).
- Performance, availability, retention, compliance, other non-functional targets: accept recommended defaults.

## Assumptions
Accept all reasonable assumptions; record them in the artifacts and keep moving. Do not stop to confirm an assumption.
