import sqlite3
con=sqlite3.connect('db.sqlite3')
cur=con.cursor()
cur.execute("PRAGMA table_info('cars_maintenancerecord')")
for col in cur.fetchall():
    print(col)
con.close()
