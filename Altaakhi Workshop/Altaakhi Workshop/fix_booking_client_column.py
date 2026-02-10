import sqlite3

DB_PATH = "db.sqlite3"


def add_client_id_column():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Check if column already exists
    cursor.execute("PRAGMA table_info(bookings_booking);")
    columns = [col[1] for col in cursor.fetchall()]
    if "client_id" in columns:
        print("Column client_id already exists.")
        conn.close()
        return
    # Add the column (nullable for now)
    cursor.execute(
        "ALTER TABLE bookings_booking ADD COLUMN client_id INTEGER REFERENCES clients_client(id)"
    )
    print("Column client_id added.")
    conn.commit()
    conn.close()


if __name__ == "__main__":
    add_client_id_column()
