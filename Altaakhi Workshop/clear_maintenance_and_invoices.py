from cars.models import MaintenanceRecord
from invoices.models import Invoice

# حذف جميع سجلات الصيانة والفواتير (بيانات تجريبية فقط)
MaintenanceRecord.objects.all().delete()
Invoice.objects.all().delete()

print("تم حذف جميع سجلات الصيانة والفواتير بنجاح.")
