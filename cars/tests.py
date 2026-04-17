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


class CarWorkshopLogicTest(TestCase):
	def setUp(self):
		from clients.models import Client
		from services.models import Department
		# create client and car
		self.client = Client.objects.create(first_name='Test', last_name='Client', phone_number='000')
		self.car = Car.objects.create(client=self.client, plate_number='UNIT-123')
		# create department/service
		dept = Department.objects.create(name='General')
		self.service = Service.objects.create(name='Oil Change', default_price=50, department=dept)

	def test_no_records(self):
		# Car with no maintenance records
		self.assertFalse(self.car.is_in_workshop())
		self.assertIsNone(self.car.get_current_record())

	def test_open_record(self):
		# create an open maintenance record (defaults to is_finished=False)
		mr = MaintenanceRecord.objects.create(car=self.car, service=self.service, price=100)
		self.assertTrue(self.car.is_in_workshop())
		current = self.car.get_current_record()
		self.assertIsNotNone(current)
		self.assertEqual(current.id, mr.id)
		self.assertFalse(current.is_finished)

	def test_finished_last_record(self):
		# create a finished maintenance record
		mr = MaintenanceRecord.objects.create(car=self.car, service=self.service, price=80, is_finished=True)
		self.assertFalse(self.car.is_in_workshop())
		self.assertIsNone(self.car.get_current_record())


class PersistenceTest(TestCase):
	"""End-to-end persistence test for items_json -> InvoiceItem -> DB

	Verifies service rows, part rows, mixed rows, and inventory decrement.
	"""
	def setUp(self):
		from clients.models import Client
		from services.models import Department
		from inventory.models import Part

		self.client_obj = Client.objects.create(first_name='Persist', last_name='Tester', phone_number='000')
		self.car = Car.objects.create(client=self.client_obj, plate_number='P-001')
		dept = Department.objects.create(name='General')
		self.service = Service.objects.create(name='Persist Service', default_price=30, department=dept)
		# create an inventory part with track_stock enabled
		self.part = Part.objects.create(name='Brake Pad', quantity=10, track_stock=True, sale_price=20)

	def test_persistence_of_items_json(self):
		import json
		from django.utils import timezone
		from invoices.models import Invoice

		today = timezone.now().date().strftime('%Y-%m-%d')

		items = [
			{
				'description': self.service.name,
				'qty': 1,
				'rate': float(self.service.default_price),
				'discount': 0,
				'service_id': self.service.id
			},
			{
				'description': self.part.name,
				'qty': 2,
				'rate': float(self.part.sale_price),
				'discount': 0,
				'part_id': self.part.id
			}
		]

		data = {
			'plate_number': self.car.plate_number,
			'maintenance_date': today,
			'notes': 'persistence test',
			'items_json': json.dumps(items)
		}

		resp = self.client.post('/maintenance/add/', data)

		# Invoice should be created for the client
		inv = Invoice.objects.filter(client=self.client_obj).order_by('-id').first()
		self.assertIsNotNone(inv, 'Invoice was not created')

		its = list(inv.items.all())
		self.assertEqual(len(its), 2, 'Invoice items count mismatch')

		# Service item should be linked correctly
		svc_items = [i for i in its if getattr(i, 'service_id', None) == self.service.id]
		self.assertTrue(svc_items, 'Service item not saved or linked')

		# Part item should be linked correctly
		part_items = [i for i in its if getattr(i, 'part_id', None) == self.part.id]
		self.assertTrue(part_items, 'Part item not saved or linked')

		# Inventory should be decremented by qty (10 -> 8)
		self.part.refresh_from_db()
		self.assertEqual(self.part.quantity, 8, 'Part quantity was not decremented')

