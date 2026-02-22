#!/usr/bin/env python3
import os
import sys
from datetime import datetime

# ensure project root is on path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()

from django.utils import timezone
from cars.models import Car
from cars.maintenance_models import MaintenanceRecord

PLATE = '70016'

try:
    car = Car.objects.get(plate_number=PLATE)
except Car.DoesNotExist:
    print(f"Car with plate {PLATE} not found")
    sys.exit(2)

# set delivery_date for any maintenance record missing it
now = timezone.now()
updated = 0
for rec in MaintenanceRecord.objects.filter(car=car, delivery_date__isnull=True):
    rec.delivery_date = now
    rec.save()
    updated += 1

# set car status to done
car.status = 'done'
car.save()

print(f"Updated car {car.plate_number} (id={car.id}) - set status='done' and delivery_date on {updated} records")
