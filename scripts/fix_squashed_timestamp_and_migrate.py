#!/usr/bin/env python3
"""Fix ordering by moving the squashed services migration timestamp earlier,
then run Django migrations.

Creates a DB backup before modifying `django_migrations`.
"""
import shutil
import sqlite3
import sys
from datetime import datetime, timedelta
import os
import subprocess


DB = os.path.join(os.getcwd(), "db.sqlite3")
BACKUP = DB + ".fix_ts.bak"


def isoparse(s):
    # sqlite may store datetimes as ISO strings; support variants
    if s is None:
        return None
    if isinstance(s, datetime):
        return s
    try:
        return datetime.fromisoformat(s)
    except Exception:
        # try without microseconds
        try:
            return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        except Exception:
            raise


def main():
    if not os.path.exists(DB):
        print("DB not found:", DB)
        sys.exit(1)

    print("Backing up DB ->", BACKUP)
    shutil.copy2(DB, BACKUP)

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        "SELECT applied FROM django_migrations WHERE app=? AND name=?",
        ("services", "0002_add_parts_and_car"),
    )
    row = cur.fetchone()
    if not row:
        print("Reference migration services.0002_add_parts_and_car not found in django_migrations. Aborting.")
        conn.close()
        sys.exit(2)

    applied_ref = isoparse(row["applied"])
    print("services.0002 applied:", applied_ref)

    new_ts = applied_ref - timedelta(seconds=1)
    new_ts_str = new_ts.strftime("%Y-%m-%d %H:%M:%S.%f")

    # show existing value for the squashed row
    cur.execute(
        "SELECT applied FROM django_migrations WHERE app=? AND name=?",
        ("services", "0001_squashed_0003_add_car_fk"),
    )
    row2 = cur.fetchone()
    print("before squashed applied:", row2["applied"] if row2 else None)

    if not row2:
        print("Squashed services migration not found; aborting.")
        conn.close()
        sys.exit(3)

    # perform the update
    cur.execute(
        "UPDATE django_migrations SET applied=? WHERE app=? AND name=?",
        (new_ts_str, "services", "0001_squashed_0003_add_car_fk"),
    )
    conn.commit()

    cur.execute(
        "SELECT applied FROM django_migrations WHERE app=? AND name=?",
        ("services", "0001_squashed_0003_add_car_fk"),
    )
    print("after squashed applied:", cur.fetchone()["applied"])

    conn.close()

    # Run migrations using same python
    print("Running Django migrate...")
    env = os.environ.copy()
    env.setdefault("DJANGO_SECRET_KEY", "devkey")
    ret = subprocess.run([sys.executable, "manage.py", "migrate", "--verbosity", "2"], env=env)
    if ret.returncode != 0:
        print("migrate failed with code", ret.returncode)
        sys.exit(ret.returncode)

    print("Done.")


if __name__ == "__main__":
    main()
