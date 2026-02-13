import sqlite3
con=sqlite3.connect('db.sqlite3')
cur=con.cursor()
cur.execute("PRAGMA table_info('invoices_invoice')")
for col in cur.fetchall():
    print(col)
con.close()
