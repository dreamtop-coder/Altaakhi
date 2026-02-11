from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from clients.models import Client as ClientModel
from cars.models import Car
from invoices.models import Invoice, Payment
from services.models import Service, Department
from audit.models import AuditLog


class ClientDeleteTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="tester2", password="pass")
        self.user.is_staff = True
        self.user.save()
        # grant model delete permissions for client and invoices/payments to default test user
        from django.contrib.auth.models import Permission
        try:
            perm_client = Permission.objects.get(codename="delete_client")
            self.user.user_permissions.add(perm_client)
        except Permission.DoesNotExist:
            pass
        try:
            perm_delete_invoice = Permission.objects.get(codename="delete_invoice")
            perm_delete_payment = Permission.objects.get(codename="delete_payment")
            self.user.user_permissions.add(perm_delete_invoice)
            self.user.user_permissions.add(perm_delete_payment)
        except Permission.DoesNotExist:
            pass
        self.client = Client()
        self.client.force_login(self.user)

    def create_sample(self):
        c = ClientModel.objects.create(
            first_name="Test",
            last_name="User",
            phone_number="12345",
            customer_id="CUST-002",
        )
        car = Car.objects.create(client=c, plate_number="PLT-002", vin_number="VIN002")
        dept = Department.objects.create(name="dept-test")
        svc = Service.objects.create(name="svc-test-2", default_price=10, department=dept)
        inv = Invoice.objects.create(invoice_number="INV-002", client=c, car=car, amount=100)
        inv.services.add(svc)
        inv.save()
        return c, car, inv

    def test_prevent_delete_client_with_paid_invoice(self):
        c, car, inv = self.create_sample()
        pay = Payment.objects.create(
            invoice=inv,
            car=car,
            client=c,
            amount=inv.amount,
            payment_date=timezone.now(),
            method="cash",
            status="paid",
        )
        inv.paid = True
        inv.save()

        url = reverse("delete_client", args=[c.id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(ClientModel.objects.filter(id=c.id).exists())
        self.assertContains(resp, "لا يمكن حذف العميل")

    def test_allow_delete_after_removing_payments_and_invoice(self):
        c, car, inv = self.create_sample()
        pay = Payment.objects.create(
            invoice=inv,
            car=car,
            client=c,
            amount=inv.amount,
            payment_date=timezone.now(),
            method="cash",
            status="paid",
        )
        inv.paid = True
        inv.save()

        del_url = reverse("delete_payment", args=[pay.id])
        resp = self.client.post(del_url)
        inv.refresh_from_db()
        self.assertFalse(inv.paid)

        inv_delete_url = reverse("delete_invoice", args=[inv.id])
        resp = self.client.post(inv_delete_url)
        self.assertFalse(Invoice.objects.filter(id=inv.id).exists())

        url = reverse("delete_client", args=[c.id])
        resp = self.client.post(url, follow=True)
        self.assertRedirects(resp, reverse("clients_list"))
        self.assertFalse(ClientModel.objects.filter(id=c.id).exists())

    def test_payments_filtering(self):
        c, car, inv = self.create_sample()
        pay = Payment.objects.create(
            invoice=inv,
            car=car,
            client=c,
            amount=inv.amount,
            payment_date=timezone.now(),
            method="cash",
            status="paid",
        )

        url = reverse("payments_list")
        resp = self.client.get(url, {"client": c.id}, HTTP_HOST="localhost")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "عرض دفعات العميل")

        resp = self.client.get(url, {"invoice": inv.id}, HTTP_HOST="localhost")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "عرض دفعات الفاتورة")

    def test_user_without_permission_cannot_delete_client(self):
        # regular user without delete permission
        c, car, inv = self.create_sample()
        user = get_user_model().objects.create_user(username="noperm", password="pass")
        self.client.force_login(user)
        resp = self.client.post(reverse("delete_client", args=[c.id]))
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(ClientModel.objects.filter(id=c.id).exists())

    def test_delete_attempt_denied_logged(self):
        c, car, inv = self.create_sample()
        user = get_user_model().objects.create_user(username="attacker", password="pass")
        self.client.force_login(user)
        resp = self.client.post(reverse("delete_client", args=[c.id]))
        self.assertEqual(resp.status_code, 403)
        exists = AuditLog.objects.filter(action="DELETE_ATTEMPT_DENIED", object_type="Client", object_id=str(c.id)).exists()
        self.assertTrue(exists, "DELETE_ATTEMPT_DENIED was not logged")

    def test_user_with_permission_can_delete_client(self):
        c, car, inv = self.create_sample()
        User = get_user_model()
        user = User.objects.create_user(username="withperm", password="pass")
        # grant delete permission
        perm = "clients.delete_client"
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename="delete_client")
        user.user_permissions.add(permission)
        user.save()
        self.client.force_login(user)
        resp = self.client.post(reverse("delete_client", args=[c.id]), follow=True)
        self.assertRedirects(resp, reverse("clients_list"))
        self.assertFalse(ClientModel.objects.filter(id=c.id).exists())

    def test_superuser_can_delete(self):
        c, car, inv = self.create_sample()
        User = get_user_model()
        superu = User.objects.create_superuser(username="admin", password="pass", email="admin@example.com")
        self.client.force_login(superu)
        resp = self.client.post(reverse("delete_client", args=[c.id]), follow=True)
        self.assertRedirects(resp, reverse("clients_list"))
        self.assertFalse(ClientModel.objects.filter(id=c.id).exists())
# Create your tests here.
