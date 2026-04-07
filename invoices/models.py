
# Create your models here.

from django.db import models
from clients.models import Client
from cars.models import Car
from services.models import Service
from decimal import Decimal

class Invoice(models.Model):
	invoice_number = models.CharField(max_length=20, unique=True)
	# short subject/description (e.g. recipient name or brief note)
	subject = models.CharField(max_length=255, blank=True, null=True)
	client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
	car = models.ForeignKey(Car, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
	TYPE_CHOICES = [
		('stock', 'Stock Sale'),
		('maintenance', 'Maintenance'),
	]
	type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='stock')
	services = models.ManyToManyField(Service, related_name='invoices')
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	paid = models.BooleanField(default=False)
	created_at = models.DateTimeField("تاريخ الإنشاء", null=True, blank=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.invoice_number

	def recalc_amount(self):
		from django.db.models import Sum
		total = self.items.aggregate(total=Sum('total'))['total'] or Decimal('0')
		# store as Decimal with 2 decimal places consistent with Invoice.amount
		# keep precision: Invoice.amount has 2 decimal places
		self.amount = total.quantize(Decimal('0.01')) if isinstance(total, Decimal) else Decimal(str(total)).quantize(Decimal('0.01'))
		self.save()

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


# Expense models
class ExpenseCategory(models.Model):
	name = models.CharField(max_length=120)
	description = models.TextField(blank=True, null=True)

	class Meta:
		verbose_name = 'Expense Category'
		verbose_name_plural = 'Expense Categories'

	def __str__(self):
		return self.name


class Expense(models.Model):
	date = models.DateField()
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name='expenses')
	payee = models.CharField(max_length=200, blank=True, null=True)
	note = models.TextField(blank=True, null=True)
	bill = models.ForeignKey('bills.Bill', on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_expenses')
	created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-date']

	def __str__(self):
		return f"{self.date} - {self.category.name} - {self.amount}"
