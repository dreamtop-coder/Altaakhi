#!/usr/bin/env python
"""Fix invoice by adding missing InvoiceItem rows from linked MaintenanceRecord entries.

Usage: python scripts/fix_invoice_items.py INV-000062
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
# ensure project root is on sys.path so `workshop` package is importable when running the script
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
django.setup()

from invoices.models import Invoice, InvoiceItem
from cars.maintenance_models import MaintenanceRecord
from django.db.models import Sum

def fix(invoice_number):
    inv = Invoice.objects.filter(invoice_number=invoice_number).first()
    if not inv:
        print('Invoice not found:', invoice_number)
        return
    print('Found invoice:', inv.id, inv.invoice_number, 'amount=', float(inv.amount))
    items = list(inv.items.all())
    print('Existing InvoiceItem count:', len(items))
    mrs = list(inv.maintenance_records.all())
    print('Linked MaintenanceRecord count:', len(mrs))

    # build totals counters
    from collections import Counter
    mr_totals = [float(getattr(m, 'price', 0) or 0) for m in mrs]
    ii_totals = [float(getattr(ii, 'total', 0) or 0) for ii in items]
    mr_count = Counter(mr_totals)
    ii_count = Counter(ii_totals)

    created = 0
    for mr in mrs:
        amt = float(getattr(mr, 'price', 0) or 0)
        # if there are fewer invoice items with this amount than maintenance records, create one
        if ii_count.get(amt, 0) < mr_count.get(amt, 0):
            try:
                InvoiceItem.objects.create(
                    invoice=inv,
                    service=getattr(mr, 'service', None),
                    description=(getattr(mr.service, 'name', None) or (mr.notes or '')),
                    quantity=1,
                    rate=amt,
                    discount=0,
                    total=amt
                )
                ii_count[amt] = ii_count.get(amt, 0) + 1
                created += 1
                print('Created InvoiceItem for MR', mr.id, 'amt=', amt)
            except Exception as e:
                print('Failed to create InvoiceItem for MR', mr.id, 'err=', e)

    # recompute invoice amount from items
    s = inv.items.aggregate(total=Sum('total'))['total'] or 0
    inv.amount = float(s)
    inv.save()
    print('Created items:', created)
    print('New invoice.amount =', float(inv.amount))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python scripts/fix_invoice_items.py <INVOICE_NUMBER>')
        sys.exit(1)
    fix(sys.argv[1])
