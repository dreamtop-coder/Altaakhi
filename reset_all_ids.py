"""
سكريبت تصفير الـ ID (auto increment) لجميع الجداول المرتبطة في قاعدة بيانات SQLite الخاصة بـ Django.
يمكن تشغيله مباشرة: `python reset_all_ids.py` أو من داخل shell.
"""

import os
import django


def main():
    # إعداد Django قبل الوصول إلى الـ DB
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "workshop.settings")
    django.setup()

    from django.db import connection

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

    print(
        "تم حذف جميع السجلات وتصفير العدادات بنجاح. يمكنك الآن إدخال بيانات جديدة وستبدأ الـ ID من 1."
    )


if __name__ == "__main__":
    main()
