import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()
from cars.maintenance_models import MaintenanceRecord
from invoices.models import Invoice

# تحديث كل سجل صيانة ليصبح is_finished=True إذا كانت الفاتورة مدفوعة
count = 0
for record in MaintenanceRecord.objects.all():
    if record.invoice and record.invoice.paid:
        if not record.is_finished:
            record.is_finished = True
            record.save()
            count += 1
print(f"تم تحديث {count} سجل صيانة إلى is_finished=True للفواتير المدفوعة.")
