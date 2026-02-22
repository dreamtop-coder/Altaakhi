import sqlite3
con=sqlite3.connect('db.sqlite3')
cur=con.cursor()
cur.execute("SELECT app, name, applied FROM django_migrations WHERE app IN ('invoices','cars') ORDER BY app,name")
for r in cur.fetchall():
    print(r)
con.close()
