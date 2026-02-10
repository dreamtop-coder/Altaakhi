from clients.models import Client
from cars.models import Car, Service

print("--- العملاء ---")
for client in Client.objects.all():
    print(f"ID: {client.id}, الاسم: {client.first_name} {client.last_name}")

print("\n--- السيارات ---")
for car in Car.objects.all():
    print(f"ID: {car.id}, اللوحة: {car.plate_number}, العميل: {car.client_id}")

print("\n--- الخدمات ---")
for service in Service.objects.all():
    print(f"ID: {service.id}, الاسم: {service.name}")
