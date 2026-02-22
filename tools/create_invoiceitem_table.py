import sqlite3
import os
DB='db.sqlite3'
if not os.path.exists(DB):
    print('DB not found:', DB)
    raise SystemExit(1)
con=sqlite3.connect(DB)
cur=con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='invoices_invoiceitem'")
if cur.fetchone():
    print('table already exists')
else:
    print('creating table invoices_invoiceitem')
    cur.execute('''CREATE TABLE invoices_invoiceitem (
        id integer primary key autoincrement,
        invoice_id integer,
        service_id integer,
        description varchar(255),
        quantity decimal(10,2) default 1,
        rate decimal(10,2) default 0,
        discount decimal(6,2) default 0,
        total decimal(12,3) default 0,
        created_at datetime
    )''')
    # create a simple index on invoice_id
    try:
        cur.execute('CREATE INDEX invoices_invoiceitem_invoice_id_idx ON invoices_invoiceitem(invoice_id)')
    except Exception:
        pass
    con.commit()
    print('created')
con.close()
