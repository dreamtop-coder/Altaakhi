from django.test import TestCase, override_settings
from django.utils import timezone
import json


class TamperTest(TestCase):
    @override_settings(CONTEXT_GUARD_ENFORCE=True)
    def test_enforce_context_guard(self):
        # Setup clients and car
        from clients.models import Client
        from cars.models import Car
        from services.models import Department, Service
        from invoices.models import Invoice

        owner = Client.objects.create(first_name='Owner', last_name='Car', phone_number='111', customer_id='C_OWNER_1')
        attacker = Client.objects.create(first_name='Attacker', last_name='Evil', phone_number='222', customer_id='C_ATTACKER_1')
        car = Car.objects.create(client=owner, plate_number='TAMPER-001')

        dept = Department.objects.create(name='General')
        svc = Service.objects.create(name='TamperSvc', default_price=5, department=dept)

        today = timezone.now().date().strftime('%Y-%m-%d')

        items = [
            {'description': 'Test item', 'qty': 1, 'rate': 5, 'discount': 0}
        ]

        data = {
            'selected_client_id': str(attacker.id),  # tampered value (should be overridden)
            'selected_client_car': '',
            'plate_number': car.plate_number,
            'maintenance_date': today,
            'items_json': json.dumps(items),
        }

        resp = self.client.post(f'/maintenance/add/?car_id={car.id}', data)

        # Enforcement is recorded to debug logs; assert enforcement occurred
        applied = False
        try:
            with open('debug_context_guard.log', 'r', encoding='utf-8') as f:
                txt = f.read()
                applied = 'ENFORCE_APPLIED' in txt
        except Exception:
            applied = False

        self.assertTrue(applied, 'ContextGuard enforcement was not applied (no ENFORCE_APPLIED in log)')

        # Also ensure the server-side POST dump shows the enforced client id (owner)
        post_dump_ok = False
        try:
            with open('debug_post_dump.log', 'r', encoding='utf-8') as f:
                txt2 = f.read()
                post_dump_ok = str(owner.id) in txt2
        except Exception:
            post_dump_ok = False

        self.assertTrue(post_dump_ok, 'Enforced selected_client_id not found in debug_post_dump.log')

        # Cleanup any created maintenance records/invoices to avoid teardown FK issues
        try:
            from .maintenance_models import MaintenanceRecord
            MaintenanceRecord.objects.all().delete()
        except Exception:
            pass
        try:
            Invoice.objects.all().delete()
        except Exception:
            pass
