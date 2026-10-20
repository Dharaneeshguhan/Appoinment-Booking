import re
import sqlite3
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.database import get_db
from app.models import SlotCreate, SlotResponse, SlotBookingRequest, BookingResponse
from app.services import (
    list_slots,
    get_slot_by_id,
    create_slot,
    book_slot,
    SlotNotFoundError,
    SlotAlreadyBookedError,
    SlotConflictError,
)

router = APIRouter(prefix="/slots", tags=["Slots"])
DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@router.get("", response_model=List[SlotResponse], summary="List appointment slots")
def get_slots(
    date: Optional[str] = Query(
        None,
        description="Filter slots by date in YYYY-MM-DD format (e.g. 2026-10-25)"
    ),
    available_only: bool = Query(
        True,
        description="If true, returns only available (unbooked) slots. Set to false to see all slots."
    ),
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    List appointment slots. By default, lists only available (unbooked) slots.
    Optionally filter by a specific date.
    """
    if date:
        date = date.strip()
        if not DATE_REGEX.match(date):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query parameter 'date' must be in YYYY-MM-DD format."
            )

    slots = list_slots(conn, slot_date=date, available_only=available_only)
    return slots


@router.get("/{slot_id}", response_model=SlotResponse, summary="Get slot details")
def get_slot(slot_id: int, conn: sqlite3.Connection = Depends(get_db)):
    """Retrieve details of an appointment slot by its ID."""
    slot = get_slot_by_id(conn, slot_id)
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment slot with ID {slot_id} not found."
        )
    return slot


@router.post("", response_model=SlotResponse, status_code=status.HTTP_201_CREATED, summary="Create a new slot")
def add_slot(slot_data: SlotCreate, conn: sqlite3.Connection = Depends(get_db)):
    """Create a new available appointment slot."""
    try:
        created = create_slot(conn, slot_data)
        return created
    except SlotConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.post(
    "/{slot_id}/book",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book a specific slot"
)
def book_slot_endpoint(
    slot_id: int,
    payload: SlotBookingRequest,
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    Book an available appointment slot by slot ID.
    Rejects the request if the slot does not exist or has already been booked.
    """
    try:
        booking = book_slot(conn, slot_id=slot_id, customer_name=payload.customer_name, notes=payload.notes)
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
