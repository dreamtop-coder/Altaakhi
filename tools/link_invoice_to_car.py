import os
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()

from invoices.models import Invoice
from cars.models import Car
from cars.maintenance_models import MaintenanceRecord
from services.models import Service
from clients.models import Client
from django.utils import timezone

inv_no = 'INV-000001'
inv = Invoice.objects.filter(invoice_number=inv_no).first()
if not inv:
    print('Invoice not found:', inv_no)
    sys.exit(1)
print('Found invoice:', inv.id, inv.invoice_number, inv.amount, 'paid=', inv.paid)

client = None
if inv.client:
    client = inv.client
else:
    client = Client.objects.filter(first_name='SMOKE', last_name__icontains='TEST').first()

if not client:
    print('Client not found for invoice. Aborting.')
    sys.exit(1)
print('Client:', client.id, client.first_name, client.last_name)

# choose first car for client
car = Car.objects.filter(client=client).order_by('id').first()
if not car:
    print('No car found for this client. Aborting.')
    sys.exit(1)
print('Selected car:', car.id, car.plate_number, car.status)

# link invoice to car if not linked
if not inv.car:
    inv.car = car
    inv.save()
    print('Linked invoice to car.')
else:
    print('Invoice already linked to car_id', inv.car.id)

# ensure a placeholder Service exists
svc_name = 'Invoice items (created)'
svc, _ = Service.objects.get_or_create(name=svc_name, defaults={'default_price': float(inv.amount or 0)})

# create maintenance record if none for this invoice
mr = MaintenanceRecord.objects.filter(invoice=inv).first()
if mr:
    print('MaintenanceRecord already exists for this invoice:', mr.id)
else:
    mr = MaintenanceRecord.objects.create(
        car=car,
        service=svc,
        price=inv.amount or 0,
        notes='Linked from INV-000001',
        created_at=timezone.now(),
        is_finished=False,
        invoice=inv
    )
    print('Created MaintenanceRecord', mr.id)

# set car.status = pending_payment if there are unpaid invoices
if Invoice.objects.filter(car=car, paid=False).exists():
    car.status = 'pending_payment'
    car.save()
    print('Set car.status = pending_payment')
else:
    print('No unpaid invoices found for car.')

print('CAR:', car.id, car.plate_number, car.status)
mrs = MaintenanceRecord.objects.filter(car=car).order_by('created_at')
print('MAINTENANCE_COUNT:', mrs.count())
for r in mrs:
    print(r.id, r.service_id, r.price, r.notes, r.created_at, r.ready_at, r.delivery_date, r.is_finished)
print('INVOICE:', inv.id, inv.invoice_number, inv.amount, inv.paid, inv.client_id, inv.car_id)
