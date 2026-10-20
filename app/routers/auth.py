import sqlite3
from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.models import UserSignup, UserLogin, UserResponse, AuthTokenResponse
from app.auth import create_access_token, get_current_user
from app.services import create_user, authenticate_user, UserConflictError

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED, summary="Patient Signup")
def signup(payload: UserSignup, conn: sqlite3.Connection = Depends(get_db)):
    """
    Registers a new patient account.
    Returns the user profile and a signed JWT bearer token.
    """
    try:
        user = create_user(
            conn=conn,
            email=payload.email,
            full_name=payload.full_name,
            password=payload.password,
            role="PATIENT"
        )
        token = create_access_token(user_id=user["id"], email=user["email"], role=user["role"])
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user
        }
    except UserConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.post("/login", response_model=AuthTokenResponse, summary="User Login")
def login(payload: UserLogin, conn: sqlite3.Connection = Depends(get_db)):
    """
    Authenticates a user (Patient, Doctor, or Administrator) with email and password.
    Returns a signed JWT access token and user profile.
    """
    user = authenticate_user(conn=conn, email=payload.email, password=payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact the administrator.",
        )

    token = create_access_token(user_id=user["id"], email=user["email"], role=user["role"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse, summary="Get Current Authenticated User")
def get_me(current_user: dict = Depends(get_current_user)):
    """Retrieve the profile and role of the currently authenticated user."""
    return current_user
