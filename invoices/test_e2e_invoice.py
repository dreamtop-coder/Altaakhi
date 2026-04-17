from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
import json
from clients.models import Client as ClientModel
from inventory.models import Part
from services.models import Service, Department
from invoices.models import Invoice, InvoiceItem

class InvoiceE2ETests(TestCase):
    def setUp(self):
        # create test client and user
        self.client = Client()
        # create a user and login
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(username='testuser', password='testpass', is_staff=True)
        self.client.force_login(self.user)
        # create a client record (match clients.Client fields)
        self.customer = ClientModel.objects.create(first_name='TestCust', phone_number='000', customer_id='TESTCUST1')
        # parts
        self.part_available = Part.objects.create(name='AvailPart', quantity=10, sale_price=50, track_stock=True, is_sale=True)
        self.part_unavailable = Part.objects.create(name='NoStockPart', quantity=0, sale_price=30, track_stock=True, is_sale=True)
        # service (create required Department)
        self.department = Department.objects.create(name='General')
        self.service = Service.objects.create(name='SvcTest', default_price=15, department=self.department)

    def post_invoice(self, items, action='save_send'):
        data = {
            'selected_client_id': str(self.customer.id),
            'items_json': json.dumps(items),
            'subject': 'E2E Test',
            'action': action,
        }
        return self.client.post('/invoices/add/', data)

    def test_happy_path_creates_invoice_and_decrements_stock(self):
        items = [
            {'part_id': self.part_available.id, 'description': self.part_available.name, 'qty': 2, 'rate': float(self.part_available.sale_price), 'discount': 0, 'amount': float(self.part_available.sale_price) * 2}
        ]
        resp = self.post_invoice(items)
        self.assertEqual(resp.status_code, 302)
        item = InvoiceItem.objects.order_by('-id').first()
        self.assertIsNotNone(item)
        self.assertEqual(item.part_id, self.part_available.id)
        self.assertEqual(item.item_type, 'part')
        self.assertEqual(float(item.quantity), 2.0)
        self.part_available.refresh_from_db()
        self.assertEqual(self.part_available.quantity, 8)

    def test_out_of_stock_does_not_create_item(self):
        items = [
            {'part_id': self.part_unavailable.id, 'description': self.part_unavailable.name, 'qty': 1, 'rate': float(self.part_unavailable.sale_price), 'discount': 0, 'amount': float(self.part_unavailable.sale_price)}
        ]
        resp = self.post_invoice(items)
        # server should respond 400 due to availability check
        self.assertEqual(resp.status_code, 400)
        # ensure no new invoice item was created
        items_count = InvoiceItem.objects.filter(part=self.part_unavailable).count()
        self.assertEqual(items_count, 0)
        self.part_unavailable.refresh_from_db()
        self.assertEqual(self.part_unavailable.quantity, 0)

    def test_missing_part_id_row_is_ignored(self):
        # post a row without part_id (should be ignored)
        items = [
            {'description': 'ManualNameOnly', 'qty': 1, 'rate': 10, 'discount': 0, 'amount': 10}
        ]
        resp = self.post_invoice(items)
        # New policy: missing `part_id` is rejected for stock invoices
        self.assertEqual(resp.status_code, 400)
        # ensure no invoice was created
        latest_inv = Invoice.objects.order_by('-id').first()
        # if no invoices exist, latest_inv may be None; ensure items count unchanged
        if latest_inv:
            self.assertEqual(latest_inv.items.count(), 0)

    def test_service_id_is_ignored_in_stock_invoice(self):
        items = [
            {'service_id': self.service.id, 'qty': 1, 'rate': float(self.service.default_price), 'description': self.service.name}
        ]
        resp = self.post_invoice(items)
        self.assertEqual(resp.status_code, 302)
        # no invoice items should be created for services in stock invoice
        latest_items = InvoiceItem.objects.filter(service=self.service).count()
        self.assertEqual(latest_items, 0)
