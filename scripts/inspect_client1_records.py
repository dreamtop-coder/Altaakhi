from clients.models import Client
from cars.maintenance_models import MaintenanceRecord
from invoices.models import Invoice

client_id = 1
plate = '75871'

try:
    c = Client.objects.get(id=client_id)
except Exception as e:
    print('Client fetch error:', e)
    raise SystemExit(1)

cars = [car for car in c.cars.all() if getattr(car, 'plate_number', None) == plate]
print('Found cars:', [ (car.id, car.plate_number) for car in cars ])
for car in cars:
    print('\n--- Car', car.id, car.plate_number, '---')
    recs = MaintenanceRecord.objects.filter(car=car).order_by('-created_at')
    if not recs:
        print('  No maintenance records')
    for r in recs:
        inv = getattr(r, 'invoice', None)
        print('  Record id:', r.id, 'created_at:', r.created_at, 'delivery_date:', r.delivery_date, 'price:', r.price, 'invoice_id:', (inv.id if inv else None))
        if inv:
            print('    Invoice id:', inv.id, 'number:', inv.invoice_number, 'inv.created_at:', inv.created_at, 'inv.amount:', inv.amount)
print('\nDone')
