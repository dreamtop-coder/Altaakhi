from django.test import TestCase, Client
from django.urls import reverse
from inventory.models import Supplier, Part
from .models import Bill, BillLine
from django.db import IntegrityError, transaction
import json
from decimal import Decimal


class BillCreationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.supplier = Supplier.objects.create(name='Test Supplier', amount=Decimal('0.00'))
        self.part = Part.objects.create(name='Test Part', code='TP-001', quantity=5, purchase_price=Decimal('0.00'))

    def test_create_bill_updates_part_and_supplier_and_totals(self):
        items = [
            {'description': self.part.name, 'qty': 2, 'rate': '10.00', 'discount': '0'}
        ]
        payload = {
            'bill_number': 'TEST-001',
            'bill_date': '2026-02-25',
            'selected_supplier_id': str(self.supplier.id),
            'items_json': json.dumps(items),
            'action': 'save_send',
        }
        resp = self.client.post('/bills/add/', data=payload, follow=True)
        # Bill created
        self.assertEqual(Bill.objects.count(), 1)
        bill = Bill.objects.first()
        self.assertEqual(bill.bill_number, 'TEST-001')
        # totals computed server-side
        self.assertEqual(bill.subtotal, Decimal('20.000'))
        self.assertEqual(bill.discount_total, Decimal('0.000'))
        self.assertEqual(bill.grand_total, Decimal('20.000'))
        # BillLine created
        self.assertEqual(BillLine.objects.count(), 1)
        line = BillLine.objects.first()
        self.assertEqual(line.description, self.part.name)
        # Part updated
        p = Part.objects.get(pk=self.part.pk)
        self.assertEqual(p.purchase_price, Decimal('10.00'))
        self.assertEqual(p.quantity, 7)  # 5 + 2
        # Supplier balance updated
        s = Supplier.objects.get(pk=self.supplier.pk)
        self.assertEqual(s.amount, Decimal('20.000'))

    def test_duplicate_bill_number_prevents_double_create(self):
        items = [{'description': self.part.name, 'qty': 1, 'rate': '5.00', 'discount': '0'}]
        payload = {
            'bill_number': 'DUP-001',
            'bill_date': '2026-02-25',
            'selected_supplier_id': str(self.supplier.id),
            'items_json': json.dumps(items),
            'action': 'save_send',
        }
        # first create
        resp1 = self.client.post('/bills/add/', data=payload, follow=True)
        self.assertEqual(Bill.objects.count(), 1)
        # attempt to create again with same bill_number should raise IntegrityError
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                self.client.post('/bills/add/', data=payload, follow=True)
        # ensure no second persistent duplicate bill was created
        self.assertEqual(Bill.objects.filter(bill_number='DUP-001').count(), 1)
