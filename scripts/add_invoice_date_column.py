import sqlite3
import os

db='db.sqlite3'
if not os.path.exists(db):
    print('DB not found')
    raise SystemExit(1)
con=sqlite3.connect(db)
cur=con.cursor()
cur.execute("PRAGMA table_info('invoices_invoice')")
cols=cur.fetchall()
colnames=[c[1] for c in cols]
print('Existing columns:', colnames)
if 'invoice_date' in colnames:
    print('invoice_date already present')
else:
    cur.execute("ALTER TABLE invoices_invoice ADD COLUMN invoice_date DATE")
    con.commit()
    print('invoice_date column added')
con.close()
