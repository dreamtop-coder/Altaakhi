from cars.models import Car
from services.models import Service
from clients.models import Client
from invoices.models import Invoice
from cars.maintenance_models import MaintenanceRecord

print("--- السيارات ---")
for car in Car.objects.all():
    print(f"ID: {car.id}, اللوحة: {car.plate_number}, العميل: {car.client_id}")

print("\n--- العملاء ---")
for client in Client.objects.all():
    print(f"ID: {client.id}, الاسم: {client.first_name} {client.last_name}")

print("\n--- الخدمات ---")
for service in Service.objects.all():
    print(f"ID: {service.id}, الاسم: {service.name}")

print("\n--- الفواتير ---")
for invoice in Invoice.objects.all():
    print(
        f"ID: {invoice.id}, رقم الفاتورة: {invoice.invoice_number}, السيارة: {invoice.car_id}, العميل: {invoice.client_id}"
    )

print("\n--- سجلات الصيانة ---")
for rec in MaintenanceRecord.objects.all():
    print(
        f"ID: {rec.id}, السيارة: {rec.car_id}, الخدمة: {rec.service_id}, الفاتورة: {rec.invoice_id}"
    )
