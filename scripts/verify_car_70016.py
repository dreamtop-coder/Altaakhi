#!/usr/bin/env python3
import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()
from cars.models import Car
c = Car.objects.filter(plate_number='70016').values('id','plate_number','status').first()
print(c)
