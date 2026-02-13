import sqlite3, os
db = os.path.join(os.getcwd(),'db.sqlite3')
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("PRAGMA table_info('cars_maintenancerecord')")
for r in cur.fetchall():
    print(r)
conn.close()
