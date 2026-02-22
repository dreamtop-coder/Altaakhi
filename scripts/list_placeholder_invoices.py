#!/usr/bin/env python
"""List placeholder invoices (amount==0, no InvoiceItem, no Payment) without modifying DB."""
import os
import sys

# Ensure project root is in path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
import django
django.setup()

from invoices.models import Invoice
from django.db.models import Count

qs = Invoice.objects.annotate(items_count=Count('items'), payments_count=Count('payments')).filter(amount__lte=0, items_count=0, payments_count=0).order_by('id')
if not qs.exists():
    print('No placeholder invoices found.')
else:
    print('Placeholder invoices: (id, invoice_number, amount, client_id, car_plate, created_at)')
    for inv in qs:
        car_plate = getattr(inv.car, 'plate_number', None)
        print(inv.id, inv.invoice_number, float(inv.amount), inv.client_id, car_plate, inv.created_at)

print('\nRun scripts/delete_placeholder_invoices.py to delete these (review before running).')
