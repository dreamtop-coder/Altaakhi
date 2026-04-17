from django.test import TransactionTestCase, Client
from django.contrib.auth.models import User

import threading
import json


class ConcurrencyTest(TransactionTestCase):

    reset_sequences = True

    def setUp(self):
        from inventory.models import Part
        from clients.models import Client

        # create a client and a part tracked in inventory
        self.client_obj = Client.objects.create(first_name='Conc', last_name='Tester', phone_number='000')
        self.part = Part.objects.create(
            name='Concurrent Part',
            quantity=10,
            sale_price=10,
            track_stock=True
        )

    def make_request(self, qty):
        c = Client()

        items = [
            {
                'description': self.part.name,
                'qty': qty,
                'rate': float(self.part.sale_price),
                'discount': 0,
                'part_id': self.part.id
            }
        ]

        payload = {
            'items_json': json.dumps(items),
            'selected_client_id': str(self.client_obj.id)
        }

        # POST to the maintenance add endpoint which applies inventory changes
        resp = c.post('/maintenance/add/', payload)
        return resp

    def test_concurrent_stock_deduction(self):
        # Two threads attempting to deduct 7 each from quantity=10
        t1 = threading.Thread(target=self.make_request, args=(7,))
        t2 = threading.Thread(target=self.make_request, args=(7,))

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        from inventory.models import Part
        p = Part.objects.get(pk=self.part.pk)

        # Final visibility for debugging
        print('Final stock:', p.quantity)

        # Stock must never go negative
        self.assertGreaterEqual(p.quantity, 0)
        # Quantity must not exceed initial
        self.assertLessEqual(p.quantity, 10)
        # Either one deduction succeeded (10 - 7 => 3) or none (still 10)
        self.assertTrue(
            p.quantity in (3, 10),
            f"Unexpected stock value: {p.quantity}"
        )

        # Ensure at most one InvoiceItem references this part (i.e., at most one successful sale)
        from invoices.models import InvoiceItem
        items_count = InvoiceItem.objects.filter(part=self.part).count()
        self.assertLessEqual(items_count, 1, f"More than one invoice item created for part: {items_count}")
