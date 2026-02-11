#!/usr/bin/env python3
"""
Copy Part -> Supplier links from a backup SQLite DB into the current DB's M2M table.
Usage: python tools/import_part_suppliers_from_backup.py [backup_db_path] [live_db_path]
Defaults: backup_db_path=db.sqlite3.bak  live_db_path=db.sqlite3

This script assumes the current DB already has the M2M table `inventory_part_suppliers`.
It inserts (part_id, supplier_id) pairs from the backup where `supplier_id` was set.
"""
import sqlite3
import sys
import os

backup = sys.argv[1] if len(sys.argv) > 1 else 'db.sqlite3.bak'
live = sys.argv[2] if len(sys.argv) > 2 else 'db.sqlite3'

if not os.path.exists(backup):
    print('Backup DB not found:', backup)
    sys.exit(1)
if not os.path.exists(live):
    print('Live DB not found:', live)
    sys.exit(1)

b = sqlite3.connect(backup)
L = sqlite3.connect(live)
try:
    bc = b.cursor()
    lc = L.cursor()
    # Check source table
    bc.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory_part';")
    if not bc.fetchone():
        print('Backup DB does not contain inventory_part table')
        sys.exit(1)
    # Fetch part -> supplier mapping from backup
    bc.execute('SELECT id, supplier_id FROM inventory_part WHERE supplier_id IS NOT NULL')
    rows = bc.fetchall()
    if not rows:
        print('No supplier links found in backup.')
        sys.exit(0)
    # Ensure target table exists
    lc.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory_part_suppliers';")
    if not lc.fetchone():
        print('Live DB does not contain inventory_part_suppliers table. Run migrations first.')
        sys.exit(1)
    inserted = 0
    for part_id, supplier_id in rows:
        # check that part exists in live DB
        lc.execute('SELECT id FROM inventory_part WHERE id=?', (part_id,))
        if not lc.fetchone():
            continue
        # check supplier exists
        lc.execute('SELECT id FROM inventory_supplier WHERE id=?', (supplier_id,))
        if not lc.fetchone():
            continue
        # avoid duplicates
        lc.execute('SELECT 1 FROM inventory_part_suppliers WHERE part_id=? AND supplier_id=?', (part_id, supplier_id))
        if lc.fetchone():
            continue
        lc.execute('INSERT INTO inventory_part_suppliers(part_id, supplier_id) VALUES(?, ?)', (part_id, supplier_id))
        inserted += 1
    L.commit()
    print(f'Inserted {inserted} supplier links into live DB.')
finally:
    b.close()
    L.close()
