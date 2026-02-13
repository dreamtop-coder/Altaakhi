import sqlite3
conn = sqlite3.connect('db.sqlite3')
rows = list(conn.execute("SELECT id, app, name, applied FROM django_migrations ORDER BY id"))
for r in rows:
    if r[1] == 'contenttypes':
        print(r)
print('\nAll contenttypes migration rows printed')
