import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()

from invoices.models import InvoiceItem

items = InvoiceItem.objects.filter(part__isnull=True)
print("Legacy Invoice Items (no part linked):")
print("Total:", items.count())
for i in items:
    print(f"ID: {i.id} | Invoice: {i.invoice_id} | Desc: {i.description} | Type: {i.item_type}")
