import sqlite3
from typing import List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.models import UserResponse, UserStatusUpdate, UserRole
from app.auth import require_roles
from app.services import (
    list_users,
    update_user_status,
    create_user,
    UserConflictError,
)

router = APIRouter(prefix="/admin", tags=["Administrator"])


class AdminCreateUserRequest(BaseModel):
    email: str
    full_name: str
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.PATIENT


@router.get("/users", response_model=List[UserResponse], summary="List All Users")
def get_users(
    current_user: dict = Depends(require_roles(["ADMIN"])),
    conn: sqlite3.Connection = Depends(get_db)
):
    """List all registered users. Restricted to Administrator."""
    return list_users(conn)


@router.patch("/users/{user_id}/status", response_model=UserResponse, summary="Toggle User Active Status")
def set_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    current_user: dict = Depends(require_roles(["ADMIN"])),
    conn: sqlite3.Connection = Depends(get_db)
):
    """Enable or disable a user account. Restricted to Administrator."""
    if current_user["id"] == user_id and not payload.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot deactivate their own account."
        )

    try:
        updated = update_user_status(conn, user_id=user_id, is_active=payload.is_active)
        return updated
    except UserConflictError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Create User With Role")
def admin_create_user(
    payload: AdminCreateUserRequest,
    current_user: dict = Depends(require_roles(["ADMIN"])),
    conn: sqlite3.Connection = Depends(get_db)
):
    """Create a user with a specific role (Doctor, Patient, Admin). Restricted to Administrator."""
    try:
        user = create_user(
            conn=conn,
            email=payload.email,
            full_name=payload.full_name,
            password=payload.password,
            role=payload.role.value
        )
        return user
    except UserConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
