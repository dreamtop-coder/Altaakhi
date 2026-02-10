import os
import django


def main():
    # إعداد Django قبل استيراد نماذج المشروع
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "workshop.settings")
    django.setup()

    from cars.models import Car
    from cars.maintenance_models import MaintenanceRecord
    from invoices.models import Invoice

    for car in Car.objects.all():
        print(f"--- سيارة: {car.plate_number} ---")
        # فحص سجلات الصيانة
        maints = MaintenanceRecord.objects.filter(car=car)
        if maints.exists():
            for m in maints:
                print(f"  صيانة: is_finished={m.is_finished}, التاريخ={m.created_at}")
        else:
            print("  لا يوجد سجل صيانة")
        # فحص الفواتير
        invoices = Invoice.objects.filter(car=car)
        if invoices.exists():
            for inv in invoices:
                print(f"  فاتورة: paid={inv.paid}, رقم الفاتورة={inv.invoice_number}")
        else:
            print("  لا يوجد فاتورة")


if __name__ == "__main__":
    main()
