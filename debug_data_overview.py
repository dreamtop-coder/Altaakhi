import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()
from cars.models import Car
from services.models import Service
from clients.models import Client
from invoices.models import Invoice
from cars.maintenance_models import MaintenanceRecord

print('--- Cars ---')
for car in Car.objects.all():
    print(f'ID: {car.id}, plate: {car.plate_number}, client_id: {car.client_id}')

print('\n--- Clients ---')
for client in Client.objects.all():
    print(f'ID: {client.id}, name: {client.first_name} {client.last_name}')

print('\n--- Services ---')
for service in Service.objects.all():
    print(f'ID: {service.id}, name: {service.name}')

print('\n--- Invoices ---')
for invoice in Invoice.objects.all():
    print(f'ID: {invoice.id}, invoice_number: {invoice.invoice_number}, car_id: {invoice.car_id}, client_id: {invoice.client_id}')

print('\n--- Maintenance Records ---')
for rec in MaintenanceRecord.objects.all():
    print(f'ID: {rec.id}, car_id: {rec.car_id}, service_id: {rec.service_id}, invoice_id: {rec.invoice_id}')
