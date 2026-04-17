import sqlite3, os, sys
db = os.path.join(os.getcwd(), 'db.sqlite3')
if not os.path.exists(db):
    print('NO_DB', db); sys.exit(1)
conn = sqlite3.connect(db)
c = conn.cursor()
try:
    c.execute("SELECT COUNT(*) FROM invoices_expense")
    print('expenses_count:', c.fetchone()[0])
except Exception as e:
    print('ERR_EXP_COUNT', e)

print('\nrecent_expenses (id,name,amount):')
try:
    for row in c.execute("SELECT id, date, amount, note FROM invoices_expense ORDER BY id DESC LIMIT 5"):
        print(row)
except Exception as e:
    print('ERR_RECENT_EXP', e)

print('\nrecurring_entries (id,name,amount,next_date,frequency,active):')
try:
    for row in c.execute("SELECT id, name, amount, next_date, frequency, active FROM invoices_recurringexpense"):
        print(row)
except Exception as e:
    print('ERR_RECUR', e)

conn.close()
