import os
import sys
from pathlib import Path
# ensure project root is on sys.path so Django settings package can be found
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','workshop.settings')
import django
django.setup()
from invoices.models import InvoiceItem
it = InvoiceItem.objects.first()
if not it:
    print('NO_INVOICE_ITEMS')
else:
    print('ITEM_ID:', it.id)
    print('ITEM_TYPE:', getattr(it, 'item_type', None))
    print('SERVICE_ID:', getattr(it, 'service_id', None))
    print('PART_ID:', getattr(it, 'part_id', None))
    print('QUANTITY:', float(it.quantity) if it.quantity is not None else None)
    print('RATE:', float(it.rate) if it.rate is not None else None)
    print('TOTAL:', float(it.total) if it.total is not None else None)
