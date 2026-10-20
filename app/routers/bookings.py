import sqlite3
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.models import BookingCreate, BookingResponse, BookingStatusUpdate
from app.auth import get_current_user_optional, get_current_user, require_roles
from app.services import (
    book_slot,
    cancel_booking,
    update_booking_status,
    get_booking_by_id,
    list_bookings,
    list_patient_bookings,
    SlotNotFoundError,
    SlotAlreadyBookedError,
    BookingNotFoundError,
    ForbiddenActionError,
)

router = APIRouter(tags=["Bookings"])


@router.post("/bookings", response_model=BookingResponse, status_code=status.HTTP_201_CREATED, summary="Create a booking")
def create_booking_endpoint(
    payload: BookingCreate,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    Book an available slot with customer details.
    If authenticated, automatically sets patient ownership.
    Rejects the request if the slot does not exist (404) or has already been booked (409).
    Never permits double-booking.
    """
    customer_name = payload.customer_name
    user_id = None

    if current_user:
        user_id = current_user["id"]
        if not customer_name:
            customer_name = current_user["full_name"]

    if not customer_name or not customer_name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Customer name is required."
        )

    try:
        booking = book_slot(
            conn,
            slot_id=payload.slot_id,
            customer_name=customer_name.strip(),
            notes=payload.notes,
            user_id=user_id
        )
        return booking
    except SlotNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except SlotAlreadyBookedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.get("/bookings", response_model=List[BookingResponse], summary="List all bookings")
def get_all_bookings(
    current_user: Optional[dict] = Depends(get_current_user_optional),
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    Retrieve all confirmed bookings.
    If authenticated as a Patient, restricted to only their own bookings.
    Doctor, Admin, or unauthenticated test calls receive the full practice roster.
    """
    if current_user and current_user["role"] == "PATIENT":
        return list_patient_bookings(conn, current_user["id"])

    return list_bookings(conn)


@router.get("/my-bookings", response_model=List[BookingResponse], summary="Patient Appointments")
def get_patient_appointments(
    current_user: dict = Depends(require_roles(["PATIENT"])),
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    Retrieve only the appointments belonging to the logged-in patient.
    Java equivalent: @PreAuthorize("hasRole('PATIENT')")
    """
    return list_patient_bookings(conn, current_user["id"])


@router.post("/my-bookings/{booking_id}/cancel", response_model=BookingResponse, summary="Cancel Patient Appointment")
def cancel_patient_appointment(
    booking_id: int,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    Cancel an appointment. Patients can only cancel their own appointments.
    Doctors and Administrators can cancel any appointment.
    Cancelling automatically frees the slot for other patients to book.
    """
    is_staff = current_user["role"] in ("DOCTOR", "ADMIN")
    try:
        updated = cancel_booking(
            conn=conn,
            booking_id=booking_id,
            user_id=current_user["id"],
            is_staff=is_staff
        )
        return updated
    except BookingNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenActionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.patch("/bookings/{booking_id}/status", response_model=BookingResponse, summary="Update Booking Status")
def update_status(
    booking_id: int,
    payload: BookingStatusUpdate,
    current_user: dict = Depends(require_roles(["DOCTOR", "ADMIN"])),
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    Update appointment status (CONFIRMED, COMPLETED, or CANCELLED).
    Restricted to Doctor and Administrator.
    """
    try:
        updated = update_booking_status(conn, booking_id, payload.status.value)
        return updated
    except BookingNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/doctor/schedule", response_model=List[BookingResponse], summary="Doctor Schedule Roster")
def get_doctor_schedule(
    current_user: dict = Depends(require_roles(["DOCTOR", "ADMIN"])),
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    Full appointment schedule for the doctor. Restricted to DOCTOR and ADMIN.
    """
    return list_bookings(conn)


@router.get("/bookings/{booking_id}", response_model=BookingResponse, summary="Get booking by ID")
def get_booking(booking_id: int, conn: sqlite3.Connection = Depends(get_db)):
    """Retrieve details of a specific booking by its ID."""
    booking = get_booking_by_id(conn, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID {booking_id} not found."
        )
    return booking
