import sqlite3, os
p = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'db.sqlite3'))
print('DB', p)
con=sqlite3.connect(p)
cur=con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
for r in cur.fetchall():
    print('TABLE', r[0])
try:
    cur.execute('SELECT count(*) FROM bills_bill;')
    print('bills_bill count', cur.fetchone()[0])
except Exception as e:
    print('bills_bill error', e)
try:
    cur.execute('SELECT id, bill_number, grand_total, status, bill_date, created_at FROM bills_bill ORDER BY id LIMIT 10;')
    for r in cur.fetchall():
        print('ROW', r)
except Exception as e:
    print('select rows error', e)
con.close()
