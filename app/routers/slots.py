import re
import sqlite3
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.database import get_db
from app.models import SlotCreate, SlotResponse, SlotBookingRequest, BookingResponse
from app.auth import get_current_user_optional, require_roles
from app.services import (
    list_slots,
    get_slot_by_id,
    create_slot,
    delete_slot,
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
def add_slot(
    slot_data: SlotCreate,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    Create a new available appointment slot.
    Allowed for Doctor, Admin, or unauthenticated backend setup.
    Rejected with 403 Forbidden if called by a Patient.
    """
    if current_user and current_user["role"] == "PATIENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patients are not authorized to create appointment slots."
        )

    try:
        created = create_slot(conn, slot_data)
        return created
    except SlotConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.delete("/{slot_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an unbooked slot")
def remove_slot(
    slot_id: int,
    current_user: dict = Depends(require_roles(["DOCTOR", "ADMIN"])),
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    Delete an unbooked appointment slot. Requires DOCTOR or ADMIN role.
    """
    try:
        delete_slot(conn, slot_id)
    except SlotNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SlotConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/{slot_id}/book",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book a specific slot"
)
def book_slot_endpoint(
    slot_id: int,
    payload: SlotBookingRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    Book an available appointment slot by slot ID.
    If authenticated as a Patient, automatically associates patient ownership.
    Rejects the request if the slot does not exist or has already been booked.
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
            slot_id=slot_id,
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
