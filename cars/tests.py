from django.test import TestCase
from django.utils import timezone

from .models import Car
from .maintenance_models import MaintenanceRecord
from services.models import Service
from .views import derive_car_status


class DerivedStatusTest(TestCase):
	def setUp(self):
		# create client and car via minimal fixtures (use existing Client model)
		from clients.models import Client
		self.client_obj = Client.objects.create(first_name='UT', last_name='User', phone_number='000')
		self.car = Car.objects.create(client=self.client_obj, plate_number='UT-TEST-1')
		# ensure a service exists
		from services.models import Department
		dept = Department.objects.create(name='General')
		self.service = Service.objects.create(name='UT Service', default_price=10, department=dept)

	def test_new_maintenance_moves_to_in_progress(self):
		# Initially no maintenance -> waiting
		self.assertEqual(derive_car_status(self.car), 'waiting')
		# Create a new (not finished) maintenance record
		mr = MaintenanceRecord.objects.create(
			car=self.car,
			service=self.service,
			price=50,
			notes='unit test',
			created_at=timezone.now(),
			is_finished=False
		)
		# Reload and assert derived status becomes in_progress
		self.car.refresh_from_db()
		self.assertEqual(derive_car_status(self.car), 'in_progress')

