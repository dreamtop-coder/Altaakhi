import sqlite3
conn = sqlite3.connect('db.sqlite3')
for r in conn.execute("SELECT id,app,name,applied FROM django_migrations ORDER BY id"):
    print(r)
