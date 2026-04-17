import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','workshop.settings_test')
import django
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

django.setup()

from invoices.models import InvoiceItem
from inventory.models import Part

items = InvoiceItem.objects.all().order_by('id')
print('InvoiceItem count:', items.count())
for ii in items:
    desc = (ii.description or '').strip()
    part = Part.objects.filter(name__iexact=desc).first() or Part.objects.filter(name__icontains=desc).first()
    part_id = part.id if part else None
    part_qty = getattr(part, 'quantity', None) if part else None
    print(ii.id, ii.invoice.invoice_number if ii.invoice else None, repr(desc), float(ii.quantity), float(ii.rate), float(ii.total), part_id, part_qty)

# Also print all parts with id, name, quantity
print('\nParts snapshot:')
for p in Part.objects.all().order_by('id'):
    print(p.id, p.name, getattr(p, 'quantity', None))
