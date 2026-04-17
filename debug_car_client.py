import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()
from clients.models import Client
from cars.models import Car

# Check for a car by plate number and its client
plate = input('Enter plate number: ')
car = Car.objects.filter(plate_number=plate).first()
if car:
    print(f"Car found: {car.plate_number}, client_id: {car.client_id}")
    client = car.client
    print(f"Client data: {client.id}, {client.first_name} {client.last_name}")
else:
    print("No car found with that plate.")

# فحص جميع السيارات والعملاء المرتبطين
for car in Car.objects.all():
    print(f"Car: {car.plate_number}, Client: {car.client_id}")
for client in Client.objects.all():
    print(f"Client: {client.id}, Cars: {client.cars.count()}")
