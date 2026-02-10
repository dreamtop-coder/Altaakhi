import os
import django


def main():
    # إعداد Django قبل استيراد نماذج المشروع
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "workshop.settings")
    django.setup()

    # استيراد الموديلات بعد تهيئة Django
    from clients.models import Client
    from cars.maintenance_models import MaintenanceRecord
    from invoices.models import Payment

    print("حذف جميع العملاء...")
    Client.objects.all().delete()
    print("حذف جميع سجلات الصيانة...")
    MaintenanceRecord.objects.all().delete()
    print("حذف جميع الإيرادات...")
    Payment.objects.all().delete()
    print("تم الحذف بنجاح.")


if __name__ == "__main__":
    main()
