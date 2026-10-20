import re
from datetime import date, time
from typing import Optional
from pydantic import BaseModel, Field, field_validator

DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_REGEX = re.compile(r"^\d{2}:\d{2}$")


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


class BookingCreate(BaseModel):
    slot_id: int = Field(
        ...,
        description="The ID of the slot to book",
        json_schema_extra={"example": 1}
    )
    customer_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Full name of the customer",
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
    def sanitize_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Customer name cannot be empty or whitespace only")
        return cleaned


class SlotBookingRequest(BaseModel):
    """Payload when booking via /slots/{slot_id}/book directly"""
    customer_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Full name of the customer",
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
    def sanitize_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Customer name cannot be empty or whitespace only")
        return cleaned


class BookingResponse(BaseModel):
    id: int
    slot_id: int
    customer_name: str
    notes: Optional[str] = None
    booked_at: str
    slot: Optional[SlotResponse] = None


class MessageResponse(BaseModel):
    detail: str
