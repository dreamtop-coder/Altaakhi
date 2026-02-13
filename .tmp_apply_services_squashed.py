import sqlite3, datetime
conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()
name = '0001_squashed_0003_add_car_fk'
cur.execute("SELECT COUNT(1) FROM sqlite_master WHERE type='table' AND name='django_migrations'")
if cur.fetchone()[0] == 0:
    raise SystemExit('No django_migrations table found; aborting')
cur.execute("SELECT COUNT(1) FROM django_migrations WHERE app='services' AND name=?", (name,))
if cur.fetchone()[0]:
    print('Row already exists for', name)
else:
    now = datetime.datetime.utcnow().isoformat()
    cur.execute("INSERT INTO django_migrations(app, name, applied) VALUES(?,?,?)", ('services', name, now))
    conn.commit()
    print('Inserted', name)
for r in conn.execute("SELECT id,app,name,applied FROM django_migrations WHERE app='services' ORDER BY id"):
    print(r)
