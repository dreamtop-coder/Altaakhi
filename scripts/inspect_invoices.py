import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()

from invoices.models import Invoice

nums = ['INV-000065', 'INV-000066', 'INV-000067', 'INV-000068']
print('--- INVOICE ITEMS AND PART STOCKS ---')
for n in nums:
    inv = Invoice.objects.filter(invoice_number=n).first()
    if not inv:
        print(n, 'NOT FOUND')
        continue
    try:
        client_name = f"{inv.client.first_name} {inv.client.last_name or ''}".strip()
    except Exception:
        client_name = 'Unknown'
    status = 'paid' if inv.paid else 'unpaid'
    print(f"INVOICE {n} (id={inv.id}) client={client_name} amount={inv.amount} status={status}")
    its = list(inv.items.all())
    if not its:
        print('  (no items)')
    for it in its:
        part = getattr(it, 'part', None)
        if part:
            part.refresh_from_db()
            print(f"  ITEM id={it.id} desc='{it.description}' qty={it.quantity} part_id={part.id} part_name='{part.name}' part_qty={part.quantity}")
        else:
            print(f"  ITEM id={it.id} desc='{it.description}' qty={it.quantity} part=None")
print('--- END ---')
