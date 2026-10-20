from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import slots, bookings, auth, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database and run migrations on startup
    init_db()
    yield


app = FastAPI(
    title="Appointment Slot Booker API",
    description=(
        "A secure single-doctor Appointment Slot Booker JSON API with Role-Based Access Control "
        "(Patient, Doctor, Administrator), password hashing, JWT authentication, and atomic double-booking prevention."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# Enable CORS for external client applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(slots.router)
app.include_router(bookings.router)
app.include_router(admin.router)


@app.get("/", tags=["General"], summary="API Root / Info")
def root():
    return {
        "service": "Appointment Slot Booker API (Single-Doctor Practice)",
        "version": "2.0.0",
        "status": "online",
        "documentation": "/docs",
        "roles": ["PATIENT", "DOCTOR", "ADMIN"],
        "endpoints": {
            "auth": {
                "signup": "POST /auth/signup",
                "login": "POST /auth/login",
                "profile": "GET /auth/me"
            },
            "slots": {
                "list_available_slots": "GET /slots?available_only=true",
                "filter_slots_by_date": "GET /slots?date=YYYY-MM-DD",
                "create_slot": "POST /slots",
                "delete_slot": "DELETE /slots/{slot_id}",
                "book_slot": "POST /slots/{slot_id}/book"
            },
            "patient": {
                "my_appointments": "GET /my-bookings",
                "cancel_appointment": "POST /my-bookings/{booking_id}/cancel"
            },
            "doctor": {
                "schedule": "GET /doctor/schedule",
                "update_appointment_status": "PATCH /bookings/{booking_id}/status"
            },
            "admin": {
                "list_users": "GET /admin/users",
                "create_user": "POST /admin/users",
                "toggle_user_status": "PATCH /admin/users/{user_id}/status"
            }
        }
    }


@app.get("/health", tags=["General"], summary="Health Check")
def health_check():
    return {"status": "healthy"}
