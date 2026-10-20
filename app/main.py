from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import init_db
from app.routers import slots, bookings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the SQLite database tables on startup
    init_db()
    yield


app = FastAPI(
    title="Appointment Slot Booker API",
    description=(
        "A JSON API for viewing available appointment slots and booking appointments. "
        "Engineered with strict atomic concurrency control to prevent double-booking."
    ),
    version="1.0.0",
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
app.include_router(slots.router)
app.include_router(bookings.router)


@app.get("/", tags=["General"], summary="API Root / Info")
def root():
    return {
        "service": "Appointment Slot Booker API",
        "version": "1.0.0",
        "status": "online",
        "documentation": "/docs",
        "endpoints": {
            "list_available_slots": "GET /slots?available_only=true",
            "filter_slots_by_date": "GET /slots?date=YYYY-MM-DD",
            "create_slot": "POST /slots",
            "book_slot_via_slot_id": "POST /slots/{slot_id}/book",
            "book_slot_via_bookings": "POST /bookings",
            "list_all_bookings": "GET /bookings"
        }
    }


@app.get("/health", tags=["General"], summary="Health Check")
def health_check():
    return {"status": "healthy"}
