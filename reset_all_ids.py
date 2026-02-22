# سكريبت تصفير الـ ID (auto increment) لجميع الجداول المرتبطة في قاعدة بيانات SQLite الخاصة بـ Django
# شغّل هذا السكريبت عبر Django shell: python manage.py shell < reset_all_ids.py

import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()
from django.db import connection

def main():
    confirm = ('--confirm' in sys.argv) or (os.environ.get('CONFIRM_CLEAR') == '1')
    print('WARNING: This script will DELETE data from key tables and reset SQLite sequences.')
    print('Run with --confirm or set CONFIRM_CLEAR=1 to proceed.')
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM cars_maintenancerecord;")
        mr_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM invoices_invoice;")
        inv_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM cars_car;")
        car_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM cars_service;")
        svc_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM clients_client;")
        client_count = cursor.fetchone()[0]

    print('Summary (counts):')
    print(f'  MaintenanceRecord: {mr_count}')
    print(f'  Invoice: {inv_count}')
    print(f'  Car: {car_count}')
    print(f'  Service: {svc_count}')
    print(f'  Client: {client_count}')

    if not confirm:
        print('No action taken. Use --confirm or set CONFIRM_CLEAR=1 to perform the reset.')
        return

    with connection.cursor() as cursor:
        # حذف جميع السجلات
        cursor.execute("DELETE FROM cars_maintenancerecord;")
        cursor.execute("DELETE FROM invoices_invoice;")
        cursor.execute("DELETE FROM cars_car;")
        cursor.execute("DELETE FROM cars_service;")
        cursor.execute("DELETE FROM clients_client;")
        # تصفير الـ auto increment (SQLite فقط)
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='cars_maintenancerecord';")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='invoices_invoice';")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='cars_car';")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='cars_service';")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='clients_client';")

    print("تم حذف جميع السجلات وتصفير العدادات بنجاح. يمكنك الآن إدخال بيانات جديدة وستبدأ الـ ID من 1.")


if __name__ == '__main__':
    main()
