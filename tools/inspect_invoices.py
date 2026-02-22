import sqlite3

DB = 'db.sqlite3'
invoice_numbers = [
    'INV-SMOKE-37-1771798908',
    'INV-SMOKE-36-1771798747',
    'INV-SMOKE-35-1771798622',
    'INV-SMOKE-34-1771798412',
    'INV-000001',
]

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()

for inv_no in invoice_numbers:
    cur.execute('SELECT id, invoice_number, amount, paid, created_at, client_id, car_id FROM invoices_invoice WHERE invoice_number=?', (inv_no,))
    inv = cur.fetchone()
    if not inv:
        print(f'Invoice not found: {inv_no}')
        continue
    print('---')
    print('INVOICE:', dict(inv))
    car_id = inv['car_id']
    if car_id:
        cur.execute('SELECT id, plate_number, status FROM cars_car WHERE id=?', (car_id,))
        car = cur.fetchone()
        print('CAR:', dict(car) if car else 'Car not found')
        if car:
            cur.execute('''SELECT id, service_id, price, notes, created_at, ready_at, delivery_date, is_finished
                           FROM cars_maintenancerecord WHERE car_id=? AND invoice_id=? ORDER BY created_at''', (car_id, inv['id']))
            mrs = cur.fetchall()
            print('MAINTENANCE_COUNT:', len(mrs))
            for r in mrs:
                print(dict(r))
    else:
        print('No car linked to this invoice')

con.close()
