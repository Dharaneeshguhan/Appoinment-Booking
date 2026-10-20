# Single-Doctor Appointment Booking System

A secure, full-stack appointment booking application for a single-doctor medical practice. Built with **FastAPI** (Python backend), a file-based **SQLite** database, and a **React + Vite** frontend. Features role-based access control for **Patients**, **Doctors**, and **Administrators**, bcrypt password hashing, JWT token authentication, and strict concurrency control preventing double-booking.

---

## Roles & Access Control

| Role | Portal / Dashboard Features | Permissions |
| :--- | :--- | :--- |
| **Patient** | Personal Dashboard | Browse free slots, book appointments (one-click with pre-filled name), view personal consultation history, and cancel own appointments. |
| **Doctor** | Doctor Portal | View upcoming patient roster, update consultation statuses (`CONFIRMED`, `COMPLETED`, `CANCELLED`), create schedule slots, and delete unbooked slots. |
| **Administrator** | Admin Console | System oversight: view and manage users, activate/deactivate accounts, create staff accounts, view master booking audit trail, and manage schedule slots. |
| **Guest / Public** | Landing Page | Browse available consultation times and sign in or create a patient account. |

---

## Architecture & Technology Stack

| Layer | Technology | Purpose | Java / Spring Boot Equivalent |
| :--- | :--- | :--- | :--- |
| **Backend API** | FastAPI (Python 3.12) | REST API endpoints, routing, CORS, validation | Spring Boot `@RestController`, Spring MVC |
| **Database** | SQLite 3 (file-based) | Relational storage with foreign keys and WAL mode | Embedded H2 / PostgreSQL + Flyway |
| **Security & Auth** | BCrypt + PyJWT | Password hashing (salt rounds=12) and signed JWT tokens | Spring Security, `BCryptPasswordEncoder`, `JwtAuthenticationFilter` |
| **Frontend SPA** | React 18 + Vite | Reactive UI with role-based dashboards | React / Angular Single Page Application |
| **Testing** | Pytest + HTTPX | Automated unit, RBAC, persistence, and concurrency tests | JUnit 5 + MockMvc / REST Assured |

---

## Project Structure

```
appointment_booker/
├── app/
│   ├── __init__.py
│   ├── config.py           # Configuration (DB path, JWT secrets, token expiry)
│   ├── database.py         # SQLite connection manager, schema setup, WAL mode & migrations
│   ├── auth.py             # BCrypt hashing, JWT generation, get_current_user & require_roles
│   ├── models.py           # Pydantic schemas (User, Slot, Booking DTOs)
│   ├── services.py         # Business logic layer with atomic SQLite write transactions
│   └── routers/
│       ├── __init__.py
│       ├── auth.py         # /auth/signup, /auth/login, /auth/me
│       ├── slots.py        # /slots endpoints (browse, create, delete, book)
│       ├── bookings.py     # /bookings, /my-bookings, /doctor/schedule, /bookings/{id}/status
│       └── admin.py        # /admin/users, /admin/users/{id}/status
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Isolated temporary SQLite fixture & TestClient
│   ├── test_auth.py        # Signup, login, invalid password, profile, deactivation tests
│   ├── test_rbac.py        # Ownership checks, role restrictions, cancellation, status updates
│   ├── test_slots.py       # Slot listing, time range, date filter tests
│   ├── test_bookings.py    # Booking workflows, 404, 409 double-booking rejection tests
│   ├── test_concurrency.py # Multithreaded race-condition stress tests (10 simultaneous threads)
│   └── test_persistence.py # Verifies data survives application server restarts
├── frontend/               # React + Vite application
│   ├── package.json        # Frontend dependencies
│   ├── vite.config.js      # Vite dev server & backend API proxy
│   ├── index.html          # HTML shell
│   └── src/
│       ├── main.jsx        # React root bootstrap
│       ├── App.jsx         # Main container rendering active dashboard by role
│       ├── App.css         # Clean, responsive styles
│       ├── api.js          # Central API client with automatic JWT Bearer token injection
│       ├── context/
│       │   └── AuthContext.jsx # React context managing user profile, token, login, logout
│       └── components/
│           ├── Header.jsx           # Navbar with role badge, user greeting, and logout
│           ├── AuthModal.jsx        # Login & Patient Sign Up modal with quick demo buttons
│           ├── PatientDashboard.jsx # Patient portal (browse slots, personal history, cancel)
│           ├── DoctorDashboard.jsx  # Doctor portal (patient roster, status toggle, slots)
│           ├── AdminDashboard.jsx   # Admin console (user management, master bookings)
│           ├── SlotList.jsx         # Grid of available slots with date filter
│           ├── BookingModal.jsx     # Booking dialog
│           └── CreateSlot.jsx       # Staff slot creation form
├── seed_users.py           # Seeds default Doctor and Administrator accounts safely
├── seed_data.py            # Seeds sample slots for upcoming days
├── run.py                  # Convenience script to start the local FastAPI server
├── requirements.txt        # Python dependencies
├── pytest.ini             # Pytest configuration
└── README.md               # Complete documentation
```

---

## Java Full Stack Developer's Mental Model

If you are coming from Java (Spring Boot / Angular), here is how every file maps to concepts you already know:

### Backend Mapping

| Python File | Spring Boot / Java Equivalent | Purpose & Description |
| :--- | :--- | :--- |
| [`requirements.txt`](requirements.txt) | `pom.xml` / `build.gradle` | Declares dependencies (`fastapi`, `uvicorn`, `pydantic`, `pytest`, `bcrypt`, `pyjwt`). |
| [`run.py`](run.py) / [`app/main.py`](app/main.py) | `@SpringBootApplication` / `Application.java` | Entry point that initializes server and registers routers. |
| [`app/auth.py`](app/auth.py) | `SecurityFilterChain` + `JwtTokenProvider` + `PasswordEncoder` | Handles BCrypt password hashing, JWT generation, and `@PreAuthorize` role checking. |
| [`app/models.py`](app/models.py) | DTO classes with Bean Validation (`@NotNull`, `@Size`, `@Email`) | Pydantic models validating request bodies and serializing JSON responses. |
| [`app/services.py`](app/services.py) | `@Service` classes with `@Transactional` | Business logic executing SQL queries with atomic SQLite locks (`BEGIN IMMEDIATE`). |
| [`app/database.py`](app/database.py) | `DataSource` / `HikariCP` + Flyway migration | Manages database connection lifecycle, tables, and migrations. |
| [`app/routers/auth.py`](app/routers/auth.py) | `AuthController` (`/auth/**`) | Public endpoints for user signup, login, and profile fetching. |
| [`app/routers/slots.py`](app/routers/slots.py) | `SlotController` (`/slots/**`) | Available slot queries, staff slot creation, and slot deletion. |
| [`app/routers/bookings.py`](app/routers/bookings.py) | `BookingController` (`/bookings/**`, `/my-bookings/**`) | Booking management, patient ownership checks, and status updates. |
| [`app/routers/admin.py`](app/routers/admin.py) | `AdminController` (`/admin/**`) | User management and account deactivation endpoints. |
| `tests/test_*.py` | JUnit 5 + MockMvc / REST Assured | Automated tests verifying authentication, RBAC, double-booking, and concurrency. |

### Frontend Mapping

| React / Vite Frontend File | Java / Full Stack Equivalent | Purpose & Description |
| :--- | :--- | :--- |
| [`frontend/package.json`](frontend/package.json) | Node build descriptor (`pom.xml`) | Defines frontend dependencies (`react`, `react-dom`, `vite`). |
| [`frontend/src/context/AuthContext.jsx`](frontend/src/context/AuthContext.jsx) | `SecurityContextHolder` (Client-side) | Holds the authenticated user's profile, role, and JWT token in React state & `localStorage`. |
| [`frontend/src/api.js`](frontend/src/api.js) | `RestTemplate` / Angular `HttpInterceptor` | Central API service that automatically attaches `Authorization: Bearer <token>` to requests. |
| [`frontend/src/App.jsx`](frontend/src/App.jsx) | Root Single Page App Container / Router | Renders the appropriate role portal based on `user.role` (`PATIENT`, `DOCTOR`, `ADMIN`). |
| [`frontend/src/components/AuthModal.jsx`](frontend/src/components/AuthModal.jsx) | Login / Registration Dialog | Modal for patient sign-up and login with quick-fill demo buttons. |
| [`frontend/src/components/PatientDashboard.jsx`](frontend/src/components/PatientDashboard.jsx) | Patient Client Portal | Allows patients to book slots, view their appointments, and cancel visits. |
| [`frontend/src/components/DoctorDashboard.jsx`](frontend/src/components/DoctorDashboard.jsx) | Doctor Staff Portal | Roster of patient appointments with status actions (`Mark Completed`, `Cancel`). |
| [`frontend/src/components/AdminDashboard.jsx`](frontend/src/components/AdminDashboard.jsx) | Admin Backoffice View | Master user management, account activation toggle, and audit trail of all bookings. |

---

## Default Accounts for Testing

The database comes pre-seeded with two staff accounts:

| Role | Email | Password | Name |
| :--- | :--- | :--- | :--- |
| **Doctor** | `doctor@clinic.com` | `Doctor@123` | Dr. Sarah Mitchell |
| **Administrator** | `admin@clinic.com` | `Admin@123` | Practice Administrator |

*Patients can create their own accounts via the **New Patient Sign Up** tab in the UI.*

---

## Windows Execution Guide

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

### Step 2: Seed Sample Data & Accounts
In your backend terminal:
```powershell
# 1. Seed Doctor and Administrator accounts
python seed_users.py

# 2. (Optional) Seed sample slots for upcoming days
python seed_data.py
```

---

### Step 3: Run Both Servers in Separate Terminals

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

## Running Automated Tests

Run the full test suite locally:
```powershell
python -m pytest -v
```

All **27 tests** will execute and pass:
- **Authentication**: Patient registration, duplicate email rejection, login, 401 unauthorized, token validation, account deactivation.
- **RBAC & Permissions**: Patient slot creation forbidden, doctor slot creation, patient booking ownership & cancellation, slot freeing upon cancellation, doctor status updates, admin user management.
- **Slot Management & Filtering**: Time sequence validation, date filtering, 404 missing slots.
- **Double-Booking Prevention**: Sequential double-booking rejection (`409 Conflict`) and 10-thread parallel race-condition stress test.
- **Persistence Across Restarts**: Verifies SQLite file records survive server restarts.
