from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
import json

class SmokeTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(username='smoketest', password='testpass', is_staff=True)
        self.client = Client()
        self.client.force_login(self.user)

        # create common fixtures
        from clients.models import Client as ClientModel
        from inventory.models import Part, Supplier
        from services.models import Service, Department

        self.customer = ClientModel.objects.create(first_name='SmokeCust', phone_number='000')
        self.supplier = Supplier.objects.create(name='SmokeSupplier', phone='111')
        self.part = Part.objects.create(name='SmokePart', quantity=5, sale_price=20, track_stock=True, is_sale=True)
        dept = Department.objects.create(name='General')
        self.service = Service.objects.create(name='SmokeService', default_price=15, department=dept)
        # create a car for maintenance flows
        from cars.models import Car
        self.car = Car.objects.create(client=self.customer, plate_number='SM-001')

    def post_bill(self, items, supplier_id=None, action='save_send'):
        data = {
            'selected_supplier_id': str(supplier_id or self.supplier.id),
            'items_json': json.dumps(items),
            'bill_date': __import__('datetime').date.today().strftime('%Y-%m-%d'),
            'bill_number': '',
            'notes': 'smoke bill',
            'action': action,
        }
        return self.client.post('/bills/add/', data)

    def post_invoice(self, items, action='save_send'):
        data = {
            'selected_client_id': str(self.customer.id),
            'items_json': json.dumps(items),
            'subject': 'Smoke Invoice',
            'action': action,
        }
        return self.client.post('/invoices/add/', data)

    def post_maintenance(self, items):
        import datetime
        today = datetime.date.today().strftime('%Y-%m-%d')
        data = {
            'plate_number': self.car.plate_number,
            'maintenance_date': today,
            'notes': 'smoke maintenance',
            'items_json': json.dumps(items),
        }
        return self.client.post('/maintenance/add/', data)

    def test_bills_add_increases_stock(self):
        # Purchase 3 units of SmokePart
        items = [{'description': self.part.name, 'qty': 3, 'rate': float(self.part.sale_price), 'discount': 0, 'amount': float(self.part.sale_price) * 3}]
        before = self.part.quantity
        resp = self.post_bill(items)
        self.assertIn(resp.status_code, (302, 303))
        self.part.refresh_from_db()
        self.assertEqual(self.part.quantity, before + 3)

    def test_invoices_reject_service_only(self):
        items = [{'service_id': self.service.id, 'qty': 1, 'rate': float(self.service.default_price), 'description': self.service.name}]
        resp = self.post_invoice(items)
        self.assertEqual(resp.status_code, 400)

    def test_maintenance_add_persists_service_and_part_and_decrements_stock(self):
        items = [
            {'description': self.service.name, 'qty': 1, 'rate': float(self.service.default_price), 'discount': 0, 'service_id': self.service.id},
            {'description': self.part.name, 'qty': 2, 'rate': float(self.part.sale_price), 'discount': 0, 'part_id': self.part.id}
        ]
        before = self.part.quantity
        resp = self.post_maintenance(items)
        # maintenance flow creates invoice and decrements stock; expect redirect
        self.assertIn(resp.status_code, (302, 303))
        self.part.refresh_from_db()
        self.assertEqual(self.part.quantity, before - 2)

if __name__ == '__main__':
    import django, os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
    django.setup()
    import unittest
    unittest.main()
