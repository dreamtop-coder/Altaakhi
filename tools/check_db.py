import sqlite3, os
DB='db.sqlite3'
print('db_exists=', os.path.exists(DB))
if os.path.exists(DB):
    conn=sqlite3.connect(DB)
    cur=conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory_purchase';")
    print('found=', cur.fetchone())
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='django_migrations';")
    print('django_migrations_table=', cur.fetchone())
    if cur.fetchone() is not None:
        pass
    try:
        cur.execute("SELECT app, name FROM django_migrations WHERE app='inventory';")
        print('applied inventory migrations=', cur.fetchall())
    except Exception as e:
        print('error querying django_migrations:', e)
    conn.close()
