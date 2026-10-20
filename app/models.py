import re
from datetime import date, time
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, field_validator

DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_REGEX = re.compile(r"^\d{2}:\d{2}$")


class UserRole(str, Enum):
    PATIENT = "PATIENT"
    DOCTOR = "DOCTOR"
    ADMIN = "ADMIN"


class BookingStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# --- User & Auth Models ---

class UserSignup(BaseModel):
    email: str = Field(..., description="Unique email address", json_schema_extra={"example": "patient@example.com"})
    password: str = Field(..., min_length=6, description="Password (minimum 6 characters)", json_schema_extra={"example": "Secret123"})
    full_name: str = Field(..., min_length=1, max_length=100, description="User's full name", json_schema_extra={"example": "Jane Doe"})

    @field_validator("email")
    @classmethod
    def sanitize_email(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if "@" not in cleaned or "." not in cleaned:
            raise ValueError("Invalid email address format")
        return cleaned

    @field_validator("full_name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Full name cannot be empty")
        return cleaned


class UserLogin(BaseModel):
    email: str = Field(..., json_schema_extra={"example": "patient@example.com"})
    password: str = Field(..., json_schema_extra={"example": "Secret123"})

    @field_validator("email")
    @classmethod
    def sanitize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserStatusUpdate(BaseModel):
    is_active: bool


# --- Slot Models ---

class SlotCreate(BaseModel):
    slot_date: str = Field(
        ...,
        description="Date of the appointment slot in YYYY-MM-DD format",
        json_schema_extra={"example": "2026-10-25"}
    )
    start_time: str = Field(
        ...,
        description="Start time in HH:MM format (24h)",
        json_schema_extra={"example": "09:00"}
    )
    end_time: str = Field(
        ...,
        description="End time in HH:MM format (24h)",
        json_schema_extra={"example": "09:30"}
    )

    @field_validator("slot_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        v = v.strip()
        if not DATE_REGEX.match(v):
            raise ValueError("slot_date must be in YYYY-MM-DD format")
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError(f"Invalid calendar date: {v}")
        return v

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        v = v.strip()
        if not TIME_REGEX.match(v):
            raise ValueError("Time must be in HH:MM format (24-hour)")
        try:
            parts = v.split(":")
            time(hour=int(parts[0]), minute=int(parts[1]))
        except ValueError:
            raise ValueError(f"Invalid time: {v}")
        return v

    @field_validator("end_time")
    @classmethod
    def validate_start_before_end(cls, end_val: str, info) -> str:
        start_val = info.data.get("start_time")
        if start_val and end_val <= start_val:
            raise ValueError("end_time must be later than start_time")
        return end_val


class SlotResponse(BaseModel):
    id: int
    slot_date: str
    start_time: str
    end_time: str
    is_booked: bool
    created_at: str


# --- Booking Models ---

class BookingCreate(BaseModel):
    slot_id: int = Field(
        ...,
        description="The ID of the slot to book",
        json_schema_extra={"example": 1}
    )
    customer_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Full name of customer (defaults to authenticated user if logged in)",
        json_schema_extra={"example": "Alice Smith"}
    )
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional booking notes",
        json_schema_extra={"example": "Initial consultation"}
    )

    @field_validator("customer_name")
    @classmethod
    def sanitize_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Customer name cannot be empty or whitespace only")
            return cleaned
        return v


class SlotBookingRequest(BaseModel):
    """Payload when booking via /slots/{slot_id}/book directly"""
    customer_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Full name of customer (defaults to authenticated user if logged in)",
        json_schema_extra={"example": "Alice Smith"}
    )
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional booking notes",
        json_schema_extra={"example": "Routine checkup"}
    )

    @field_validator("customer_name")
    @classmethod
    def sanitize_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Customer name cannot be empty or whitespace only")
            return cleaned
        return v


class BookingStatusUpdate(BaseModel):
    status: BookingStatus = Field(..., description="Updated booking status")


class BookingResponse(BaseModel):
    id: int
    slot_id: int
    customer_name: str
    notes: Optional[str] = None
    booked_at: str
    user_id: Optional[int] = None
    status: str = "CONFIRMED"
    slot: Optional[SlotResponse] = None


class MessageResponse(BaseModel):
    detail: str
