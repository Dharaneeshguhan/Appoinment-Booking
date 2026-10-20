import sqlite3
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.models import BookingCreate, BookingResponse
from app.services import (
    book_slot,
    get_booking_by_id,
    list_bookings,
    SlotNotFoundError,
    SlotAlreadyBookedError,
)

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED, summary="Create a booking")
def create_booking_endpoint(
    payload: BookingCreate,
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    Book an available slot with customer details.
    Rejects the request if the slot does not exist (404) or has already been booked (409).
    Never permits double-booking.
    """
    try:
        booking = book_slot(
            conn,
            slot_id=payload.slot_id,
            customer_name=payload.customer_name,
            notes=payload.notes
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


@router.get("", response_model=List[BookingResponse], summary="List all bookings")
def get_all_bookings(conn: sqlite3.Connection = Depends(get_db)):
    """Retrieve all confirmed bookings, ordered newest first."""
    return list_bookings(conn)


@router.get("/{booking_id}", response_model=BookingResponse, summary="Get booking by ID")
def get_booking(booking_id: int, conn: sqlite3.Connection = Depends(get_db)):
    """Retrieve details of a specific booking by its ID."""
    booking = get_booking_by_id(conn, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID {booking_id} not found."
        )
    return booking
