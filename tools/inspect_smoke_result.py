import sqlite3
from decimal import Decimal

DB = 'db.sqlite3'
plate = 'SMOKE98408'

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()

# Find car
cur.execute("SELECT id, plate_number, status FROM cars_car WHERE plate_number=?", (plate,))
car = cur.fetchone()
if not car:
    print('Car not found:', plate)
    exit(0)
print('CAR:', dict(car))

car_id = car['id']

# Maintenance records
cur.execute('''SELECT id, service_id, price, notes, created_at, ready_at, delivery_date, is_finished, invoice_id
               FROM cars_maintenancerecord WHERE car_id=? ORDER BY created_at''', (car_id,))
mrs = cur.fetchall()
print('MAINTENANCE_COUNT:', len(mrs))
for r in mrs:
    print(dict(r))

# Invoices related to this car via maintenance records
cur.execute('''SELECT i.id, i.invoice_number, i.amount, i.paid, i.created_at
               FROM invoices_invoice i
               JOIN cars_maintenancerecord m ON m.invoice_id = i.id
               WHERE m.car_id = ?
               GROUP BY i.id''', (car_id,))
inv_rows = cur.fetchall()
print('INVOICES_LINKED_COUNT:', len(inv_rows))
for inv in inv_rows:
    print(dict(inv))

# Any invoices with no maintenance but maybe linked by car_id placeholder (if exists)
try:
    cur.execute('SELECT id, invoice_number, amount, paid, created_at FROM invoices_invoice WHERE car_id=?', (car_id,))
    inv_by_car = cur.fetchall()
    if inv_by_car:
        print('INVOICES_DIRECT_COUNT:', len(inv_by_car))
        for inv in inv_by_car:
            print(dict(inv))
except Exception:
    pass

con.close()
