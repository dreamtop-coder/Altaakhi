from django.test import TestCase
from inventory.models import Supplier, Part
from .services import migrate_session_bill
from .models import Bill, BillLine
from decimal import Decimal


class SessionMigrationTests(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.create(name='MigrSupplier', amount=Decimal('0.00'))
        self.part = Part.objects.create(name='MigrPart', code='MP-01', quantity=10, purchase_price=Decimal('2.00'))

    def test_migrate_session_bill_success(self):
        session_bill = {
            'number': 'MIG-001',
            'date': '2026-02-20',
            'vendor_id': str(self.supplier.id),
            'vendor_name': self.supplier.name,
            'notes': 'migrated',
            'items': [
                {'description': self.part.name, 'qty': 3, 'rate': '5.00', 'discount': '0'}
            ],
            'status': 'sent'
        }
        bill, reason = migrate_session_bill(session_bill)
        self.assertIsNotNone(bill)
        self.assertIsNone(reason)
        # verify DB records
        self.assertEqual(Bill.objects.filter(bill_number='MIG-001').count(), 1)
        self.assertEqual(BillLine.objects.filter(bill__bill_number='MIG-001').count(), 1)
        p = Part.objects.get(pk=self.part.pk)
        self.assertEqual(p.purchase_price, Decimal('5.00'))
        self.assertEqual(p.quantity, 13)
        s = Supplier.objects.get(pk=self.supplier.pk)
        self.assertEqual(s.amount, Decimal('15.000'))

    def test_migrate_session_bill_idempotent(self):
        session_bill = {
            'number': 'MIG-002',
            'date': '2026-02-20',
            'vendor_id': str(self.supplier.id),
            'vendor_name': self.supplier.name,
            'items': [
                {'description': self.part.name, 'qty': 1, 'rate': '7.00', 'discount': '0'}
            ],
            'status': 'sent'
        }
        bill1, r1 = migrate_session_bill(session_bill)
        self.assertIsNotNone(bill1)
        bill2, r2 = migrate_session_bill(session_bill)
        self.assertIsNone(bill2)
        self.assertEqual(r2, 'exists')
