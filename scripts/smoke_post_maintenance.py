#!/usr/bin/env python
import os
import sys
from pathlib import Path

# set up django env
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()

from django.test import Client
from django.utils import timezone
from datetime import date
import json

# create minimal required objects: Department, Service, Part, Client, Car
from services.models import Department, Service
from inventory.models import Part as InvPart
from clients.models import Client as ClientModel
from cars.models import Car
from invoices.models import Invoice
from cars.maintenance_models import MaintenanceRecord

# ensure names unique
dept, _ = Department.objects.get_or_create(name='Test Dept')
svc, _ = Service.objects.get_or_create(name='Test Service X', defaults={'default_price': 100.00, 'department': dept})
# create inventory part with same name
p, _ = InvPart.objects.get_or_create(name=svc.name, defaults={'quantity': 10, 'sale_price': 100.00, 'department': dept})

# create client
import time
uniq = str(int(time.time()))[-5:]
client, _ = ClientModel.objects.get_or_create(first_name='Smoke', last_name='Tester'+uniq, phone_number='000'+uniq, customer_id='SMOKE'+uniq)
# create car with unique plate to ensure no preexisting maintenance
plate = 'SMOKE-'+uniq
car, _ = Car.objects.get_or_create(client=client, plate_number=plate, defaults={'status':'active'})

print('Setup: Service id', svc.pk, 'Part id', p.pk, 'Car id', car.pk)

c = Client()

# craft POST data
parts_list = [
    {'id': p.pk, 'name': p.name, 'qty': 1, 'unit': float(p.sale_price or 0), 'is_service': True}
]
post_data = {
    'plate_number': car.plate_number,
    'service': '',
    'price': '',
    'notes': 'smoke test',
    'maintenance_date': date.today().isoformat(),
    'service_parts': json.dumps(parts_list),
}

resp = c.post('/maintenance/add/', data=post_data, HTTP_HOST='localhost')
print('POST status_code', resp.status_code)
print('Response length', len(resp.content))
try:
    print(resp.content.decode('utf-8')[:2000])
except Exception:
    print('<binary response>')

# check maintenance record
from cars.maintenance_models import MaintenanceRecord as MR
m = MR.objects.order_by('-id').first()
if m:
    print('Maintenance created id', m.pk, 'service_id', getattr(m.service, 'pk', None), 'service_name', getattr(m.service, 'name', None), 'created_at', getattr(m, 'created_at', None))
else:
    print('No maintenance record found')

print('Total maintenance count:', MR.objects.count())
# print latest invoice for car
inv = Invoice.objects.filter(car=car).order_by('-id').first()
if inv:
    print('Invoice id', inv.pk, 'amount', inv.amount, 'services:', list(inv.services.values_list('id', flat=True)))
else:
    print('No invoice')
