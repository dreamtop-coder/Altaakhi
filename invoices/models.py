
# Create your models here.

from django.db import models
from clients.models import Client
from cars.models import Car
from services.models import Service

class Invoice(models.Model):
	invoice_number = models.CharField(max_length=20, unique=True)
	client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
	car = models.ForeignKey(Car, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
	services = models.ManyToManyField(Service, related_name='invoices')
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	paid = models.BooleanField(default=False)
	created_at = models.DateTimeField("تاريخ الإنشاء", null=True, blank=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.invoice_number

from services.models import Service

class Payment(models.Model):
	STATUS_CHOICES = [
		('paid', 'مدفوع'),
		('unpaid', 'غير مدفوع'),
		('partial', 'جزئي'),
	]
	METHOD_CHOICES = [
		('cash', 'نقدي'),
		('card', 'بطاقة'),
		('benefit', 'بنفت'),
		('bank', 'تحويل بنكي'),
		('other', 'أخرى'),
	]

	invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
	service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
	car = models.ForeignKey('cars.Car', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
	client = models.ForeignKey('clients.Client', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	payment_date = models.DateTimeField()
	method = models.CharField(max_length=10, choices=METHOD_CHOICES, default='cash')
	status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='paid')
	reference = models.CharField(max_length=20, blank=True, null=True)
	notes = models.TextField(blank=True, null=True)

	def __str__(self):
		return f"{self.amount} - {self.payment_date}"


class InvoiceItem(models.Model):
	invoice = models.ForeignKey('Invoice', on_delete=models.CASCADE, related_name='items')
	service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoice_items')
	description = models.CharField(max_length=255, blank=True, null=True)
	quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
	rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	discount = models.DecimalField(max_digits=6, decimal_places=2, default=0)
	total = models.DecimalField(max_digits=12, decimal_places=3, default=0)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		desc = self.description or (self.service.name if self.service else '')
		return f"{desc} - {self.quantity} x {self.rate} = {self.total}"
