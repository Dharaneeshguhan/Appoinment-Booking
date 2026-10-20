# Appointment Slot Booker API

A lightweight, robust Appointment Slot Booker JSON API built with **FastAPI** and **SQLite**. It allows users and staff of an appointment-based service to view available time slots and book appointments, with guaranteed atomic double-booking prevention.

---

## Features & Behaviors

- **List Available Slots**: Query appointment slots with optional date filtering (`?date=YYYY-MM-DD`). Defaults to unbooked slots (`?available_only=true`).
- **Book a Slot**: Book an available slot by providing customer details. Supports booking either via `POST /slots/{slot_id}/book` or `POST /bookings`.
- **Double-Booking Prevention**: Engineered with atomic SQLite write transactions (`BEGIN IMMEDIATE`) and a database-level `UNIQUE(slot_id)` constraint, making it impossible for two concurrent requests to double-book the same slot.
- **Slot Management**: Create new appointment slots with validation ensuring `end_time > start_time` and no overlapping duplicate time intervals.
- **Booking Management**: Inspect booking details by booking ID or list all past and upcoming bookings.
- **Clear Status Codes & Error Handling**:
  - `200 OK` / `201 Created` on success.
  - `400 Bad Request` on invalid query formatting.
  - `404 Not Found` if a slot or booking does not exist.
  - `409 Conflict` when trying to book an already-booked slot or duplicate slot creation.
  - `422 Unprocessable Entity` on validation errors (e.g. empty customer name, malformed date/time).

---

## Architecture & Technology Stack

| Component | Choice | Reason |
| :--- | :--- | :--- |
| **Framework** | FastAPI | High performance, automatic OpenAPI documentation, schema validation via Pydantic |
| **Database** | SQLite3 (File-based) | Zero installation overhead, ACID transactions, cross-platform portability |
| **Validation** | Pydantic v2 | Robust type checking, string sanitization, ISO date/time validation |
| **Testing** | Pytest + HTTPX | Fast in-memory/isolated SQLite testing with multithreaded concurrency tests |

---

## Double-Booking Prevention Mechanism

The service protects against race conditions at two distinct layers:

1. **Database Constraint Layer**: The `bookings` table defines `slot_id INTEGER NOT NULL UNIQUE`. If any parallel connection attempts to insert a second booking for the same `slot_id`, SQLite raises an `IntegrityError`.
2. **Transaction Lock Layer (`BEGIN IMMEDIATE`)**: During booking, the API initiates a write transaction using `BEGIN IMMEDIATE`. This immediately acquires a reserved write lock on SQLite, ensuring that between reading slot availability and executing the update, no other thread or process can modify the slot.

A multithreaded test (`tests/test_concurrency.py`) validates this: 10 parallel threads simultaneously attempting to book the exact same slot result in exactly 1 success (`201 Created`) and 9 rejections (`409 Conflict`).

---

## Project Structure

```
appointment_booker/
├── app/
│   ├── __init__.py
│   ├── config.py           # Configuration (database path, settings)
│   ├── database.py         # SQLite connection manager, schema setup, WAL mode
│   ├── models.py           # Pydantic schemas (Request/Response validation)
│   ├── services.py         # Core business logic & atomic transaction handling
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── slots.py        # /slots endpoints
│   │   └── bookings.py     # /bookings endpoints
│   └── main.py             # FastAPI app initialization, CORS, route registration
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Pytest fixtures with temporary isolated SQLite DB
│   ├── test_slots.py       # Slot management & filtering tests
│   ├── test_bookings.py    # Booking creation, 404, 409 conflict, and validation tests
│   └── test_concurrency.py # Multithreaded race-condition stress tests
├── seed_data.py            # Utility script to pre-populate slots for the next 3 days
├── run.py                  # Convenience script to start the local uvicorn server
├── requirements.txt        # Python dependencies
├── pytest.ini             # Pytest configuration
├── README.md               # Documentation & usage guide
└── frontend/               # React + Vite frontend application
    ├── package.json        # Frontend dependencies & build scripts
    ├── vite.config.js      # Vite dev server & proxy configuration
    ├── index.html          # HTML template
    └── src/
        ├── main.jsx        # React application entrypoint
        ├── App.jsx         # Root component managing views, state, and alerts
        ├── App.css         # UI stylesheet (responsive cards, grid, modals)
        ├── api.js          # API service client for communicating with FastAPI
        └── components/
            ├── Header.jsx       # Brand navigation & tab buttons
            ├── SlotList.jsx     # Available slots grid with date filter
            ├── BookingModal.jsx # Customer booking modal dialog
            ├── BookingsList.jsx # Persistent confirmed bookings table
            └── CreateSlot.jsx   # Staff slot creation form
```

---

## Getting Started on Windows

### Prerequisites
- **Python 3.10+** (tested on 3.12)
- **Node.js 18+** & npm (tested on Node v22)

---

### Step 1: Install Dependencies

#### Backend (Terminal 1)
```powershell
pip install -r requirements.txt
```

#### Frontend (Terminal 2)
```powershell
cd frontend
npm install
```

---

### Step 2: Seed Sample Appointment Slots (Optional)
In your backend terminal, populate initial available appointment slots for the upcoming 3 days:
```powershell
python seed_data.py
```

---

### Step 3: Run the Application (Separate Terminals)

#### Terminal 1 — Start the FastAPI Backend:
```powershell
python run.py
```
- Backend API running at: `http://127.0.0.1:8000`
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`

#### Terminal 2 — Start the React Frontend:
```powershell
cd frontend
npm run dev
```
- Frontend application running at: `http://localhost:3000`

Open your web browser and navigate to **`http://localhost:3000`**.

---

## Running Automated Backend Tests

Run the full pytest suite locally:
```powershell
python -m pytest -v
```

All 16 tests will execute:
- Unit tests for slot creation and time validation
- Date filtering tests
- Booking workflows, 404 missing slot, and 409 double-booking rejection
- Multithreaded race-condition concurrency tests (10 simultaneous threads)
- Persistence test verifying bookings survive server restarts


---

## API Reference & Examples

### 1. List Available Slots
Retrieve slots that are currently free.

```bash
# Get all available slots
curl -X GET "http://127.0.0.1:8000/slots"

# Filter by a specific date
curl -X GET "http://127.0.0.1:8000/slots?date=2026-10-25"

# Include already-booked slots
curl -X GET "http://127.0.0.1:8000/slots?available_only=false"
```

**Response (`200 OK`)**:
```json
[
  {
    "id": 1,
    "slot_date": "2026-10-25",
    "start_time": "09:00",
    "end_time": "09:30",
    "is_booked": false,
    "created_at": "2026-10-20 10:15:00"
  }
]
```

---

### 2. Create a New Slot
Staff can add slots for customers to book.

```bash
curl -X POST "http://127.0.0.1:8000/slots" \
  -H "Content-Type: application/json" \
  -d '{
    "slot_date": "2026-10-25",
    "start_time": "14:00",
    "end_time": "14:30"
  }'
```

**Response (`201 Created`)**:
```json
{
  "id": 8,
  "slot_date": "2026-10-25",
  "start_time": "14:00",
  "end_time": "14:30",
  "is_booked": false,
  "created_at": "2026-10-20 10:16:00"
}
```

---

### 3. Book an Appointment Slot
Book a slot using either `/slots/{slot_id}/book` or `/bookings`.

```bash
# Option A: Direct slot booking endpoint
curl -X POST "http://127.0.0.1:8000/slots/1/book" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Alice Cooper",
    "notes": "Consultation"
  }'

# Option B: Bookings resource endpoint
curl -X POST "http://127.0.0.1:8000/bookings" \
  -H "Content-Type: application/json" \
  -d '{
    "slot_id": 1,
    "customer_name": "Alice Cooper",
    "notes": "Consultation"
  }'
```

**Success Response (`201 Created`)**:
```json
{
  "id": 1,
  "slot_id": 1,
  "customer_name": "Alice Cooper",
  "notes": "Consultation",
  "booked_at": "2026-10-20 10:18:22",
  "slot": {
    "id": 1,
    "slot_date": "2026-10-25",
    "start_time": "09:00",
    "end_time": "09:30",
    "is_booked": true,
    "created_at": "2026-10-20 10:15:00"
  }
}
```

**Error Responses**:
- **Already Booked (`409 Conflict`)**:
  ```json
  {
    "detail": "Appointment slot with ID 1 has already been booked."
  }
  ```
- **Slot Not Found (`404 Not Found`)**:
  ```json
  {
    "detail": "Appointment slot with ID 999 does not exist."
  }
  ```
- **Invalid Name (`422 Unprocessable Entity`)**:
  ```json
  {
    "detail": [
      {
        "loc": ["body", "customer_name"],
        "msg": "Customer name cannot be empty or whitespace only",
        "type": "value_error"
      }
    ]
  }
  ```

---

### 4. List and Retrieve Bookings
Inspect existing confirmed appointments.

```bash
# List all confirmed bookings
curl -X GET "http://127.0.0.1:8000/bookings"

# Get a single booking by ID
curl -X GET "http://127.0.0.1:8000/bookings/1"
```

---

## Java Full Stack Developer's Mental Model

If you are coming from Java (Spring Boot / Jakarta EE), here is how every Python component in this project maps directly to concepts you already know:

### Backend Mapping

| Python Project File | Spring Boot / Java Equivalent | Purpose & Description |
| :--- | :--- | :--- |
| [`requirements.txt`](requirements.txt) | `pom.xml` (Maven) / `build.gradle` | Lists third-party dependencies (`fastapi`, `uvicorn`, `pydantic`, `pytest`). |
| [`run.py`](run.py) / [`app/main.py`](app/main.py) | `@SpringBootApplication` / `Application.java` | Entry point that boots the web server (like embedded Tomcat in Spring Boot). |
| [`app/routers/slots.py`](app/routers/slots.py)<br>[`app/routers/bookings.py`](app/routers/bookings.py) | `@RestController`<br>`@RequestMapping("/slots")` | API route controllers handling incoming HTTP requests, paths, parameters, and HTTP response codes. |
| [`app/models.py`](app/models.py) | DTO classes with Bean Validation (`@NotNull`, `@Pattern`, `@Size`) | Pydantic models that automatically parse and validate JSON request bodies and serialize responses. |
| [`app/services.py`](app/services.py) | `@Service` classes with `@Transactional` | Business logic layer executing database queries, managing ACID transactions, and throwing domain exceptions. |
| [`app/database.py`](app/database.py) | `DataSource` / `HikariCP` configuration + Flyway `schema.sql` | Manages SQLite database connection lifecycles, creates schema tables, and configures WAL mode. |
| `FastAPI Depends(get_db)` | `@Autowired` / Spring Dependency Injection | Automatically injects an active database connection per-request into router functions. |
| [`tests/conftest.py`](tests/conftest.py) | `@TestConfiguration` / Test Fixture | Sets up an isolated SQLite database and test HTTP client before running test cases. |
| [`tests/test_*.py`](tests/) | JUnit 5 + MockMvc / REST Assured tests | Automated assertions verifying endpoints, status codes, and concurrency safety. |

### Frontend Mapping

| React / Vite Frontend File | Java / Full Stack Equivalent | Purpose & Description |
| :--- | :--- | :--- |
| [`frontend/package.json`](frontend/package.json) | Frontend `pom.xml` / Node build configuration | Defines frontend dependencies (`react`, `react-dom`, `vite`). |
| [`frontend/vite.config.js`](frontend/vite.config.js) | Webpack / Spring Boot reverse proxy config | Configures the local dev server and reverse proxy routing `/api` calls to the FastAPI backend. |
| [`frontend/src/api.js`](frontend/src/api.js) | Spring `RestTemplate` / Angular `HttpService` | Central client service handling HTTP calls (`GET`, `POST`), serializing JSON payloads, and parsing error codes (400, 404, 409, 422). |
| [`frontend/src/App.jsx`](frontend/src/App.jsx) | Root Single Page App Container / Angular `AppComponent` | Holds application-level state (slots, bookings, active tab, notification alerts). |
| [`frontend/src/components/SlotList.jsx`](frontend/src/components/SlotList.jsx) | JSP / Thymeleaf table & filter component | Displays available slot cards and date filter control. |
| [`frontend/src/components/BookingModal.jsx`](frontend/src/components/BookingModal.jsx) | Modal Dialog / Form component | Captures customer name and notes, triggers the booking API call, and handles error states. |
| [`frontend/src/components/BookingsList.jsx`](frontend/src/components/BookingsList.jsx) | Admin / Staff management report view | Displays all persistent bookings from SQLite. |
| [`frontend/src/components/CreateSlot.jsx`](frontend/src/components/CreateSlot.jsx) | Admin slot creation form | Provides a UI to create new appointment slots calling `POST /slots`. |


---

## Assumptions & Recorded Decisions

1. **Stack**: Python 3.12 with FastAPI and built-in SQLite file storage (`appointment_booker.db`).
2. **Concurrency**: SQLite WAL mode and immediate transactions (`BEGIN IMMEDIATE`) plus a `UNIQUE` constraint on `bookings.slot_id` provide double-booking prevention without needing external distributed lock engines.
3. **Authentication**: None per specification.
4. **Time & Date Representation**: ISO 8601 strings (`YYYY-MM-DD` for dates, `HH:MM` in 24-hour format for times, UTC timestamps for `created_at` and `booked_at`).
5. **Slot Ordering**: Slot listings default to ascending chronological order (`slot_date ASC, start_time ASC`).

