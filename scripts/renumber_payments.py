import os
import shutil
import sqlite3
import time
from datetime import datetime

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'db.sqlite3'))
BACKUP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

if not os.path.exists(DB_PATH):
    print('Database file not found:', DB_PATH)
    raise SystemExit(1)

# backup
ts = datetime.now().strftime('%Y%m%dT%H%M%S')
backup_path = os.path.join(BACKUP_DIR, f'db.sqlite3.backup.{ts}')
print('Backing up', DB_PATH, '->', backup_path)
shutil.copy2(DB_PATH, backup_path)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

try:
    cur.execute('PRAGMA foreign_keys=OFF;')
    conn.commit()

    # find tables that have a column named payment_id
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cur.fetchall()]
    payment_related_tables = []
    for t in tables:
        try:
            cur.execute(f'PRAGMA table_info("{t}");')
            cols = [r['name'] for r in cur.fetchall()]
            if 'payment_id' in cols:
                payment_related_tables.append(t)
        except Exception:
            continue

    print('Tables with payment_id:', payment_related_tables)

    # fetch payments ordered by payment_date, created_at, id
    cur.execute("SELECT id FROM bills_billpayment ORDER BY payment_date ASC, id ASC;")
    rows = [r['id'] for r in cur.fetchall()]
    if not rows:
        print('No payments found; nothing to do.')
        conn.commit()
        raise SystemExit(0)

    print(f'Found {len(rows)} payments. Assigning temporary negative ids to avoid conflicts...')

    # Step 1: assign temporary negative ids and update references
    for old_id in rows:
        temp_id = -old_id
        cur.execute('UPDATE bills_billpayment SET id = ? WHERE id = ?;', (temp_id, old_id))
        for t in payment_related_tables:
            cur.execute(f'UPDATE "{t}" SET payment_id = ? WHERE payment_id = ?;', (temp_id, old_id))
    conn.commit()

    # Step 2: assign new sequential ids starting from 1
    mapping = {}  # old -> new
    new_id = 1
    for old_id in rows:
        temp_id = -old_id
        cur.execute('UPDATE bills_billpayment SET id = ? WHERE id = ?;', (new_id, temp_id))
        for t in payment_related_tables:
            cur.execute(f'UPDATE "{t}" SET payment_id = ? WHERE payment_id = ?;', (new_id, temp_id))
        mapping[old_id] = new_id
        new_id += 1
    conn.commit()

    # Update sqlite_sequence for bills_billpayment
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence';")
    if cur.fetchone():
        cur.execute('UPDATE sqlite_sequence SET seq = ? WHERE name = ?;', (new_id-1, 'bills_billpayment'))
        if cur.rowcount == 0:
            cur.execute('INSERT INTO sqlite_sequence(name, seq) VALUES(?,?);', ('bills_billpayment', new_id-1))
    conn.commit()

    print('Renumbering complete. Mapping (old -> new) for first 20 items:')
    for k in list(mapping.keys())[:20]:
        print(k, '->', mapping[k])
    print('Total payments renumbered:', len(mapping))
    print('Backup is at:', backup_path)

finally:
    try:
        cur.execute('PRAGMA foreign_keys=ON;')
        conn.commit()
    except Exception:
        pass
    conn.close()

print('Done')
