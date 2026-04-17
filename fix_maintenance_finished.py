import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()
from cars.maintenance_models import MaintenanceRecord
from invoices.models import Invoice

# Update maintenance records: set is_finished=True when related invoice is paid
count = 0
for record in MaintenanceRecord.objects.all():
    if record.invoice and record.invoice.paid:
        if not record.is_finished:
            record.is_finished = True
            record.save()
            count += 1
print(f"Updated {count} maintenance records to is_finished=True for paid invoices.")
