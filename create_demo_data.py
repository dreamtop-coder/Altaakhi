import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()
from clients.models import Client
from cars.models import Car, Service
from django.utils import timezone

# create demo client
client, _ = Client.objects.get_or_create(
    first_name='عميل',
    last_name='تجريبي',
    phone_number='0500000000',
    customer_id='CUST001'
)

# create demo car linked to client
car, _ = Car.objects.get_or_create(
    client=client,
    plate_number='1234ABC',
    year=2022
)

# create demo service
service, _ = Service.objects.get_or_create(
    name='Full Inspection',
    sale_price=100.0
)
print('Demo client, car and service created successfully.')
