# إعداد بيئة Django
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
django.setup()

from clients.models import Client
from cars.maintenance_models import MaintenanceRecord
from invoices.models import Payment
import sys
import os

def run():
    confirm = ('--confirm' in sys.argv) or (os.environ.get('CONFIRM_CLEAR') == '1')
    print("This script will DELETE all Clients, MaintenanceRecord, and Payments.")
    print('Run with --confirm or set CONFIRM_CLEAR=1 to proceed.')
    print('Summary (counts):')
    print('  Clients:', Client.objects.count())
    print('  MaintenanceRecord:', MaintenanceRecord.objects.count())
    print('  Payments:', Payment.objects.count())
    if not confirm:
        print('No destructive action taken. Pass --confirm to actually delete.')
        return
    print("حذف جميع العملاء...")
    Client.objects.all().delete()
    print("حذف جميع سجلات الصيانة...")
    MaintenanceRecord.objects.all().delete()
    print("حذف جميع الإيرادات...")
    Payment.objects.all().delete()
    print("تم الحذف بنجاح.")

if __name__ == "__main__":
    run()