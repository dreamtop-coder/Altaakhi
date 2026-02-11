from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from clients.models import Client as ClientModel
from cars.models import Car
from invoices.models import Invoice, Payment
from services.models import Service


class ClientDeleteTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="tester2", password="pass")
        self.user.is_staff = True
        self.user.save()
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
        svc = Service.objects.create(name="svc-test-2", sale_price=10)
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
# Create your tests here.
