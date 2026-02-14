#!/usr/bin/env python3
"""Apply missing squashed migration markers to django_migrations safely.

Usage (PowerShell):
  & ".\venv\Scripts\Activate.ps1"
  python .\scripts\apply_squashed_marks.py

The script is idempotent: it will skip already-present rows.
It requires a recent DB backup before running.
"""
import sqlite3
from pathlib import Path

DB = Path('db.sqlite3')
if not DB.exists():
    raise SystemExit('db.sqlite3 not found in repo root')

rows = [
    ('cars', '0001_squashed_0004_maintenancerecord_maintenance_date', '2026-02-12 22:26:54.227995'),
    ('inventory', '0001_squashed_0007_part_track_purchases_part_track_sales', '2026-02-12 22:26:54.231023'),
    ('services', '0001_squashed_0003_add_car_fk', '2026-02-12T22:37:33.761122'),
]

con = sqlite3.connect(str(DB))
cur = con.cursor()

cur.execute("PRAGMA foreign_keys=OFF")

for app,name,applied in rows:
    cur.execute("SELECT 1 FROM django_migrations WHERE app=? AND name=?", (app, name))
    if cur.fetchone():
        print(f"SKIP existing: {app}.{name}")
        continue
    print(f"INSERT: {app}.{name} @ {applied}")
    cur.execute(
        "INSERT INTO django_migrations(app,name,applied) VALUES(?,?,?)",
        (app, name, applied),
    )

con.commit()
con.close()
print('Done.')
