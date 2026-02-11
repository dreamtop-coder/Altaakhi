from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from clients.models import Client as ClientModel
from cars.models import Car
from invoices.models import Invoice, Payment
from audit.models import AuditLog
from services.models import Service, Department


class AuditLogDeleteTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="audit_tester", password="pass")
        self.user.is_staff = True
        self.user.save()
        self.client = Client()
        self.client.force_login(self.user)

    def create_sample(self):
        c = ClientModel.objects.create(
            first_name="Audit",
            last_name="Client",
            phone_number="000",
            customer_id="AUD-001",
        )
        car = Car.objects.create(client=c, plate_number="AUD-PLT", vin_number="AUDVIN")
        dept = Department.objects.create(name="audit-dept")
        svc = Service.objects.create(name="audit-svc", default_price=5, department=dept)
        inv = Invoice.objects.create(invoice_number="AUD-INV-1", client=c, car=car, amount=50)
        inv.services.add(svc)
        inv.save()
        return c, car, inv

    def test_auditlog_on_delete_payment(self):
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
        self.assertEqual(resp.status_code, 302)  # redirect to payments_list
        exists = AuditLog.objects.filter(action="DELETE_PAYMENT", object_id=str(pay.id)).exists()
        self.assertTrue(exists, "AuditLog entry for payment deletion not created")

    def test_auditlog_on_delete_invoice(self):
        c, car, inv = self.create_sample()
        # ensure no maintenance records
        inv_delete_url = reverse("delete_invoice", args=[inv.id])
        resp = self.client.post(inv_delete_url)
        # after deletion, audit log should exist
        exists = AuditLog.objects.filter(action="DELETE_INVOICE", object_id=str(inv.id)).exists()
        self.assertTrue(exists, "AuditLog entry for invoice deletion not created")

    def test_auditlog_on_delete_client(self):
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

        # delete payment
        self.client.post(reverse("delete_payment", args=[pay.id]))
        inv.refresh_from_db()
        self.assertFalse(inv.paid)
        # delete invoice
        self.client.post(reverse("delete_invoice", args=[inv.id]))
        # delete client
        self.client.post(reverse("delete_client", args=[c.id]))

        exists = AuditLog.objects.filter(action="DELETE_CLIENT", object_id=str(c.id)).exists()
        self.assertTrue(exists, "AuditLog entry for client deletion not created")
