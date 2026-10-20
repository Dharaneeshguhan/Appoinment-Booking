"""
Utility script to seed the database with initial appointment slots.
"""
from datetime import date, timedelta
from app.database import init_db, get_connection


def seed():
    init_db()
    conn = get_connection()
    try:
        today = date.today()
        sample_days = [today + timedelta(days=i) for i in range(1, 4)]

        # Sample time slots
        daily_times = [
            ("09:00", "09:30"),
            ("09:30", "10:00"),
            ("10:00", "10:30"),
            ("11:00", "11:30"),
            ("14:00", "14:30"),
            ("15:00", "15:30"),
            ("16:00", "16:30"),
        ]

        inserted = 0
        for day in sample_days:
            date_str = day.isoformat()
            for start, end in daily_times:
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO slots (slot_date, start_time, end_time) VALUES (?, ?, ?)",
                        (date_str, start, end)
                    )
                    inserted += 1
                except Exception as e:
                    print(f"Skipping ({date_str}, {start}): {e}")

        print(f"Successfully processed seed slots for {len(sample_days)} days.")
    finally:
        conn.close()


if __name__ == "__main__":
    seed()
