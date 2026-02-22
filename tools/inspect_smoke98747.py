import sqlite3
DB = 'db.sqlite3'
plate = 'SMOKE98747'
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()
cur.execute("SELECT id, plate_number, status FROM cars_car WHERE plate_number=?", (plate,))
car = cur.fetchone()
if not car:
    print('Car not found:', plate); exit(0)
print('CAR:', dict(car))
car_id = car['id']
cur.execute('''SELECT id, service_id, price, notes, created_at, ready_at, delivery_date, is_finished, invoice_id FROM cars_maintenancerecord WHERE car_id=? ORDER BY created_at''', (car_id,))
mrs = cur.fetchall()
print('MAINTENANCE_COUNT:', len(mrs))
for r in mrs:
    print(dict(r))
cur.execute('''SELECT i.id, i.invoice_number, i.amount, i.paid, i.created_at FROM invoices_invoice i JOIN cars_maintenancerecord m ON m.invoice_id = i.id WHERE m.car_id = ? GROUP BY i.id''', (car_id,))
inv_rows = cur.fetchall()
print('INVOICES_LINKED_COUNT:', len(inv_rows))
for inv in inv_rows:
    print(dict(inv))
con.close()
