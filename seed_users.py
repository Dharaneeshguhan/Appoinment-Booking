"""
Seeds default Doctor and Administrator accounts into SQLite if they do not already exist.
Safe and idempotent.
"""
import os
from app.database import init_db, get_connection
from app.services import create_user, UserConflictError


DEFAULT_DOCTOR_EMAIL = os.getenv("DOCTOR_EMAIL", "doctor@clinic.com")
DEFAULT_DOCTOR_PASSWORD = os.getenv("DOCTOR_PASSWORD", "Doctor@123")
DEFAULT_DOCTOR_NAME = os.getenv("DOCTOR_NAME", "Dr. Sarah Mitchell")

DEFAULT_ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@clinic.com")
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@123")
DEFAULT_ADMIN_NAME = os.getenv("ADMIN_NAME", "Practice Administrator")


def seed_users():
    init_db()
    conn = get_connection()
    try:
        # 1. Seed Doctor
        cursor = conn.execute("SELECT id FROM users WHERE email = ?", (DEFAULT_DOCTOR_EMAIL,))
        if not cursor.fetchone():
            create_user(
                conn,
                email=DEFAULT_DOCTOR_EMAIL,
                full_name=DEFAULT_DOCTOR_NAME,
                password=DEFAULT_DOCTOR_PASSWORD,
                role="DOCTOR"
            )
            print(f"Doctor account created: {DEFAULT_DOCTOR_EMAIL} (Password: {DEFAULT_DOCTOR_PASSWORD})")
        else:
            print(f"Doctor account already exists: {DEFAULT_DOCTOR_EMAIL}")

        # 2. Seed Administrator
        cursor = conn.execute("SELECT id FROM users WHERE email = ?", (DEFAULT_ADMIN_EMAIL,))
        if not cursor.fetchone():
            create_user(
                conn,
                email=DEFAULT_ADMIN_EMAIL,
                full_name=DEFAULT_ADMIN_NAME,
                password=DEFAULT_ADMIN_PASSWORD,
                role="ADMIN"
            )
            print(f"Admin account created: {DEFAULT_ADMIN_EMAIL} (Password: {DEFAULT_ADMIN_PASSWORD})")
        else:
            print(f"Admin account already exists: {DEFAULT_ADMIN_EMAIL}")

    finally:
        conn.close()


if __name__ == "__main__":
    seed_users()
