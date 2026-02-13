import sqlite3
import os

db='db.sqlite3'
if not os.path.exists(db):
    print('db.sqlite3 not found')
    raise SystemExit(1)
conn=sqlite3.connect(db)
cur=conn.cursor()
print('id | app | name | applied')
for row in cur.execute('SELECT id, app, name, applied FROM django_migrations ORDER BY id'):
    print('{} | {} | {} | {}'.format(*row))
conn.close()
