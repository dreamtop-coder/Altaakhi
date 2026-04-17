import sqlite3, shutil, time, os, sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB = os.path.join(BASE, 'db.sqlite3')
if not os.path.exists(DB):
    print('Database file not found:', DB)
    sys.exit(1)

bak = DB + '.backup.' + time.strftime('%Y%m%dT%H%M%S')
shutil.copy(DB, bak)
print('Backup created:', bak)

tables = ['invoices_invoice', 'invoices_expense', 'invoices_recurringexpense']
conn = sqlite3.connect(DB)
cur = conn.cursor()
for t in tables:
    try:
        cur.execute('SELECT MAX(id) FROM {}'.format(t))
        maxid = cur.fetchone()[0] or 0
    except Exception as e:
        print(f'Table {t} not found or error: {e}')
        continue
    # sqlite_sequence exists only if AUTOINCREMENT used; try to update/insert
    try:
        cur.execute('SELECT seq FROM sqlite_sequence WHERE name=?', (t,))
        row = cur.fetchone()
        if row is None:
            cur.execute('INSERT INTO sqlite_sequence(name, seq) VALUES(?, ?)', (t, maxid))
            action = 'inserted'
        else:
            cur.execute('UPDATE sqlite_sequence SET seq=? WHERE name=?', (maxid, t))
            action = 'updated'
        print(f'{t}: max_id={maxid}, sqlite_sequence {action}')
    except Exception as e:
        # if sqlite_sequence missing (rare), try to create table
        print(f'Notice: could not update sqlite_sequence for {t}: {e}')
conn.commit()
conn.close()
print('Done.')
