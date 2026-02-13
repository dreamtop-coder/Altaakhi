import sqlite3
conn = sqlite3.connect('db.sqlite3')
rows = list(conn.execute("SELECT id, app, name, applied FROM django_migrations ORDER BY id"))
for r in rows:
    if r[1] == 'services':
        print(r)
print('\nAll services migration rows printed')
