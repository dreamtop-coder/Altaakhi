#!/usr/bin/env python
"""Delete placeholder invoices (amount==0, no InvoiceItem, no Payment).
CAUTION: This permanently deletes Invoice rows and related empty InvoiceItem rows.
Run only after reviewing output from list_placeholder_invoices.py and making a DB backup.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
import django
django.setup()

from invoices.models import Invoice
from django.db.models import Count

qs = Invoice.objects.annotate(items_count=Count('items'), payments_count=Count('payments')).filter(amount__lte=0, items_count=0, payments_count=0).order_by('id')
if not qs.exists():
    print('No placeholder invoices to delete.')
else:
    print('About to delete the following placeholder invoices:')
    for inv in qs:
        print(inv.id, inv.invoice_number, float(inv.amount), inv.client_id, getattr(inv.car,'plate_number',None), inv.created_at)
    confirm = input('Type DELETE to confirm removal of these invoices: ')
    if confirm == 'DELETE':
        ids = [inv.id for inv in qs]
        Invoice.objects.filter(id__in=ids).delete()
        print(f'Deleted {len(ids)} invoices.')
    else:
        print('Aborted. No changes made.')
