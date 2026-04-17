import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()
from invoices.models import InvoiceItem

wrong_service_items = InvoiceItem.objects.filter(item_type='part', service_id__isnull=False)
wrong_part_items = InvoiceItem.objects.filter(item_type='service', part_id__isnull=False)

print('Wrong service as part:', wrong_service_items.count())
print('Sample IDs (service while part):', list(wrong_service_items.values_list('id', flat=True)[:20]))
print('Wrong part as service:', wrong_part_items.count())
print('Sample IDs (part while service):', list(wrong_part_items.values_list('id', flat=True)[:20]))

# Also report orphan items (neither service nor part)
orphan_items = InvoiceItem.objects.filter(service_id__isnull=True, part_id__isnull=True)
print('Orphan items (no service/part):', orphan_items.count())
print('Sample orphan IDs:', list(orphan_items.values_list('id', flat=True)[:20]))
