import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','workshop.settings')
import django
django.setup()
from django.test import Client
from cars.models import Car
from services.models import Service
from invoices.models import InvoiceItem, Invoice

c = Client()
# pick first car that has a client
car = Car.objects.filter(client__isnull=False).first()
if not car:
    print('NO_CAR'); raise SystemExit(1)
svc = Service.objects.first()
if not svc:
    print('NO_SERVICE'); raise SystemExit(1)

before_items = InvoiceItem.objects.count()
print('before_items=', before_items)

post_data = {
    'plate_number': car.plate_number,
    'service': str(svc.id),
    'price': '123.45',
    'notes': 'Test maintenance via automated test',
    'maintenance_date': '2026-03-09',
    'action': 'save'
}
resp = c.post('/maintenance/add/', post_data, HTTP_HOST='localhost', follow=True)
print('status_code=', resp.status_code)
# After POST, check invoice items count
after_items = InvoiceItem.objects.count()
print('after_items=', after_items)
inv = Invoice.objects.order_by('-id').first()
if inv:
    print('last_invoice:', inv.id, inv.invoice_number, inv.amount, list(inv.items.all().values('id','description','total')))
else:
    print('no invoice created')
