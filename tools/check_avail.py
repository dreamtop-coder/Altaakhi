import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','workshop.settings_test')
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import django
django.setup()
from invoices.models import Invoice
from inventory.models import Part
from inventory.utils import check_items_availability

inv = Invoice.objects.filter(invoice_number='INV-AJAX-TEST').first()
part = Part.objects.filter(name__iexact='Turbo').first()
print('inv', inv.id if inv else None, 'part', part.id if part else None, 'part.qty', getattr(part,'quantity',None))
existing_map = {}
from decimal import Decimal
for ex in inv.items.all():
    existing_map[(ex.description or '').strip().lower()] = existing_map.get((ex.description or '').strip().lower(), Decimal('0')) + Decimal(str(ex.quantity or 0))
print('existing_map', existing_map)
items = [{'part_id': part.id, 'description': part.name, 'qty': 10}]
# normalize as view does
from inventory.utils import find_part_for_description
normalized = []
for it in items:
    desc = (it.get('description') or '').strip()
    pid = it.get('part_id') or it.get('part') or None
    p = None
    if pid:
        try:
            p = Part.objects.filter(id=int(pid)).first()
            if p:
                desc = p.name
        except Exception:
            p = None
    if not p and desc:
        p = find_part_for_description(desc)
    normalized.append({'description': desc, 'qty': it.get('qty')})
print('normalized', normalized)
print('shortages', check_items_availability(normalized, existing_map))
