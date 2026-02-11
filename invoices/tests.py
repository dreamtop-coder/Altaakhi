from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from clients.models import Client as ClientModel
from cars.models import Car
from invoices.models import Invoice, Payment
from services.models import Service, Department
from audit.models import AuditLog


class InvoiceDeleteDeniedTests(TestCase):
	def setUp(self):
		User = get_user_model()
		self.user = User.objects.create_user(username="inv_tester", password="pass")
		self.client = Client()
		self.client.force_login(self.user)

	def create_sample(self):
		c = ClientModel.objects.create(first_name="Inv", last_name="Client", phone_number="000", customer_id="INV-001")
		car = Car.objects.create(client=c, plate_number="INV-PLT", vin_number="VININV")
		dept = Department.objects.create(name="dept-inv")
		svc = Service.objects.create(name="inv-svc", default_price=5, department=dept)
		inv = Invoice.objects.create(invoice_number="INV-1", client=c, car=car, amount=50)
		inv.services.add(svc)
		inv.save()
		return c, car, inv

	def test_delete_invoice_attempt_denied_logged(self):
		c, car, inv = self.create_sample()
		resp = self.client.post(reverse("delete_invoice", args=[inv.id]))
		self.assertEqual(resp.status_code, 403)
		exists = AuditLog.objects.filter(action="DELETE_ATTEMPT_DENIED", object_type="Invoice", object_id=str(inv.id)).exists()
		self.assertTrue(exists)

	def test_delete_payment_attempt_denied_logged(self):
		c, car, inv = self.create_sample()
		pay = Payment.objects.create(invoice=inv, car=car, client=c, amount=inv.amount, payment_date=timezone.now(), method="cash", status="paid")
		resp = self.client.post(reverse("delete_payment", args=[pay.id]))
		self.assertEqual(resp.status_code, 403)
		exists = AuditLog.objects.filter(action="DELETE_ATTEMPT_DENIED", object_type="Payment", object_id=str(pay.id)).exists()
		self.assertTrue(exists)

