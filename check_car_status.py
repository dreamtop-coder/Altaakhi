import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()
from cars.models import Car
from cars.maintenance_models import MaintenanceRecord
from invoices.models import Invoice

for car in Car.objects.all():
    print(f"--- Car: {car.plate_number} ---")
    # inspect maintenance records
    maints = MaintenanceRecord.objects.filter(car=car)
    if maints.exists():
        for m in maints:
            print(f"  Maintenance: is_finished={m.is_finished}, created_at={m.created_at}")
    else:
        print("  No maintenance records")
    # فحص الفواتير
    invoices = Invoice.objects.filter(car=car)
    if invoices.exists():
        for inv in invoices:
            print(f"  Invoice: paid={inv.paid}, invoice_number={inv.invoice_number}")
    else:
        print("  No invoices")
