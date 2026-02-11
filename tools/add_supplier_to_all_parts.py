#!/usr/bin/env python3
"""
Assign a supplier to all existing parts using Django ORM.

Usage:
  python tools/add_supplier_to_all_parts.py <supplier_id>

Make sure to run with the virtualenv active and set `DJANGO_SECRET_KEY` if needed:
  $env:DJANGO_SECRET_KEY='devkey'
  venv\Scripts\python.exe tools\add_supplier_to_all_parts.py 1
"""
import os
import sys

if len(sys.argv) < 2:
    print('Usage: python tools/add_supplier_to_all_parts.py <supplier_id>')
    sys.exit(1)

supplier_id = sys.argv[1]

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()

from inventory.models import Part, Supplier

try:
    sup = Supplier.objects.get(id=supplier_id)
except Supplier.DoesNotExist:
    print('Supplier id not found:', supplier_id)
    sys.exit(1)

parts = Part.objects.all()
count = 0
for p in parts:
    p.suppliers.add(sup)
    count += 1

print(f'Added supplier {sup.id} ({sup.name}) to {count} parts.')
