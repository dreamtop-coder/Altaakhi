import os, sqlite3
proj = os.path.abspath('.')
db = os.path.join(proj, 'db.sqlite3')
print('DB path:', db, 'exists=', os.path.exists(db))
if not os.path.exists(db):
    raise SystemExit(0)
con = sqlite3.connect(db)
cur = con.cursor()
cur.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','index') ORDER BY type,name")
rows = cur.fetchall()
for name, typ in rows:
    print(f"{typ}: {name}")
con.close()
