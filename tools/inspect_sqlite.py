import sqlite3, json, os

db = os.path.abspath('db.sqlite3')
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print('DB', db)
print('TABLES', tables)
if 'invoices_expense' in tables:
    cur.execute('SELECT id,date,amount,status,category_id,note FROM invoices_expense ORDER BY id DESC LIMIT 10')
    rows = cur.fetchall()
    print('ROWS', json.dumps(rows, ensure_ascii=False, default=str))
else:
    print('no invoices_expense table')
conn.close()
