import sqlite3

DB_PATH = "db.sqlite3"


def add_plate_number_column():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Check if column already exists
    cursor.execute("PRAGMA table_info(bookings_booking);")
    columns = [col[1] for col in cursor.fetchall()]
    if "plate_number" in columns:
        print("Column plate_number already exists.")
        conn.close()
        return
    # Add the column (nullable for now)
    cursor.execute(
        "ALTER TABLE bookings_booking ADD COLUMN plate_number VARCHAR(20) NULL"
    )
    print("Column plate_number added.")
    conn.commit()
    conn.close()


if __name__ == "__main__":
    add_plate_number_column()
