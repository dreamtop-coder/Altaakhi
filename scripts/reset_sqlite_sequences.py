#!/usr/bin/env python3
import sqlite3
import os
import sys

DB = 'db.sqlite3'
if not os.path.exists(DB):
    print('ERROR: db.sqlite3 not found in current directory', file=sys.stderr)
    sys.exit(1)

conn = sqlite3.connect(DB)
cur = conn.cursor()
# tables to reset (adjust if your table names differ)
tables = [
    'clients_client',
    'invoices_invoice',
    'cars_car',
    'invoices_invoiceitem',
    'invoices_payment',
]
for t in tables:
    try:
        cur.execute("DELETE FROM sqlite_sequence WHERE name=?", (t,))
    except Exception as e:
        print(f'Warning clearing sequence for {t}: {e}', file=sys.stderr)
conn.commit()
conn.close()

# VACUUM to shrink file and apply sequence changes
try:
    conn = sqlite3.connect(DB)
    conn.execute('VACUUM;')
    conn.close()
    print('sequences cleared & VACUUM done')
except Exception as e:
    print('VACUUM failed:', e, file=sys.stderr)
    sys.exit(1)
