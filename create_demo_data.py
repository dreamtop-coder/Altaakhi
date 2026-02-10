import os
import django


def main():
    # تأكد من إعداد إعدادات Django قبل استيراد نماذج المشروع
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "workshop.settings")
    django.setup()

    from clients.models import Client
    from cars.models import Car, Service

    # إنشاء عميل تجريبي
    client, _ = Client.objects.get_or_create(
        first_name="عميل",
        last_name="تجريبي",
        phone_number="0500000000",
        customer_id="CUST001",
    )

    # إنشاء سيارة مرتبطة بالعميل
    car, _ = Car.objects.get_or_create(client=client, plate_number="1234ABC", year=2022)

    # إنشاء خدمة تجريبية
    service, _ = Service.objects.get_or_create(name="فحص شامل", sale_price=100.0)

    print("تم إنشاء عميل وسيارة وخدمة تجريبية بنجاح.")


if __name__ == "__main__":
    main()
