# إعداد بيئة Django
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
django.setup()

from clients.models import Client
from cars.maintenance_models import MaintenanceRecord
from invoices.models import Payment

def run():
    print("حذف جميع العملاء...")
    Client.objects.all().delete()
    print("حذف جميع سجلات الصيانة...")
    MaintenanceRecord.objects.all().delete()
    print("حذف جميع الإيرادات...")
    Payment.objects.all().delete()
    print("تم الحذف بنجاح.")

if __name__ == "__main__":
    run()