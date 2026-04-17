
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
	amount = models.DecimalField(max_digits=10, decimal_places=3)
	paid = models.BooleanField(default=False)
	created_at = models.DateTimeField("تاريخ الإنشاء", null=True, blank=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.invoice_number

	def recalc_amount(self):
		from django.db.models import Sum
		total = self.items.aggregate(total=Sum('total'))['total'] or Decimal('0')
		# store as Decimal with 3 decimal places to match item precision
		self.amount = total.quantize(Decimal('0.001')) if isinstance(total, Decimal) else Decimal(str(total)).quantize(Decimal('0.001'))
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
	part = models.ForeignKey('inventory.Part', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoice_items')
	description = models.CharField(max_length=255, blank=True, null=True)
	# quantity and rate keep Decimal to avoid breaking existing calculations; use 3 decimal places
	quantity = models.DecimalField(max_digits=10, decimal_places=3, default=1)
	rate = models.DecimalField(max_digits=10, decimal_places=3, default=0)
	discount = models.DecimalField(max_digits=6, decimal_places=3, default=0)
	total = models.DecimalField(max_digits=12, decimal_places=3, default=0)
	ITEM_TYPE_CHOICES = [
		('service', 'Service'),
		('part', 'Part'),
	]
	item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES, default='part')
	created_at = models.DateTimeField(auto_now_add=True)

	def clean(self):
		from django.core.exceptions import ValidationError
		# Prevent selecting both service and part
		if self.service and self.part:
			raise ValidationError("لا يمكن اختيار Service و Part معاً")
		# Require at least one of service or part
		if not self.service and not self.part:
			raise ValidationError("يجب اختيار Service أو Part")
		# item_type must match the linked field
		if self.service and self.item_type != 'service':
			raise ValidationError("item_type غير مطابق للخدمة")
		if self.part and self.item_type != 'part':
			raise ValidationError("item_type غير مطابق للقطعة")

	def save(self, *args, **kwargs):
		# Force consistency: service wins over part; set rate from linked object
		if self.service:
			self.item_type = 'service'
			try:
				self.rate = self.service.default_price or self.rate
			except Exception:
				pass
			# clear part when service present
			self.part = None
		elif self.part:
			self.item_type = 'part'
			try:
				self.rate = self.part.sale_price or self.rate
			except Exception:
				pass
			# clear service when part present
			self.service = None

		# compute total honoring discount percentage if present
		try:
			q = Decimal(str(self.quantity or 0))
			r = Decimal(str(self.rate or 0))
			d = Decimal(str(self.discount or 0))
		except Exception:
			q = Decimal('0')
			r = Decimal('0')
			d = Decimal('0')
		line_total = q * r * (Decimal('1') - (d / Decimal('100')))
		# round to 3 decimal places
		try:
			self.total = line_total.quantize(Decimal('0.001'))
		except Exception:
			self.total = Decimal(str(round(float(line_total), 3)))
		super().save(*args, **kwargs)

	def __str__(self):
		desc = self.description or (self.service.name if self.service else (self.part.name if self.part else ''))
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
	amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
	category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name='expenses')
	payee = models.CharField(max_length=200, blank=True, null=True)
	note = models.TextField(blank=True, null=True)
	bill = models.ForeignKey('bills.Bill', on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_expenses')
	created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	STATUS_CHOICES = [
		('draft', 'Draft'),
		('posted', 'Posted'),
	]
	status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='posted')

	class Meta:
		ordering = ['-date']

	def __str__(self):
		return f"{self.date} - {self.category.name} - {self.amount}"


# Recurring expenses (e.g. monthly salaries, rent)
class RecurringExpense(models.Model):
	FREQUENCY_CHOICES = [
		('daily', 'Daily'),
		('weekly', 'Weekly'),
		('monthly', 'Monthly'),
		('yearly', 'Yearly'),
	]

	name = models.CharField(max_length=200)
	amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
	category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name='recurrings')
	frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='monthly')
	interval = models.PositiveIntegerField(default=1, help_text='Interval multiplier for frequency (e.g. 2 -> every 2 months)')
	start_date = models.DateField()
	end_date = models.DateField(null=True, blank=True)
	next_date = models.DateField()
	active = models.BooleanField(default=True)
	# Optional payee fields: store recipient name and/or month for salaries
	payee = models.CharField(max_length=200, blank=True, null=True)
	payee_recipient = models.CharField(max_length=200, blank=True, null=True)
	payee_month = models.CharField(max_length=20, blank=True, null=True)
	note = models.TextField(blank=True, null=True)
	created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	last_run = models.DateTimeField(null=True, blank=True)
	reminder_only = models.BooleanField(default=False, help_text='If set, create a draft reminder expense instead of a posted expense')
	# If True this recurring entry represents a flexible/planned item
	# that should NOT be auto-created on its next_date. Flexible items
	# are used for planning/expected expenses but the actual Expense
	# is created manually when the amount is known.
	is_flexible = models.BooleanField(default=False, help_text='If set, do not auto-create Expense on next_date')
	# Allows toggling whether non-flexible recurings are auto-created
	auto_create = models.BooleanField(default=True, help_text='If False, do not auto-create Expense even when not flexible')

	class Meta:
		ordering = ['-start_date']

	def __str__(self):
		return f"{self.name} - {self.amount} ({self.frequency})"

	def create_expense(self, user=None):
		"""Create an Expense row for this recurring entry.
		Returns the created Expense instance.
		This centralizes reminder vs posted logic so other callers
		(can call this method instead of duplicating behavior).
		"""
		from .models import Expense as _Expense
		# If this recurring is a reminder-only or flexible planned item,
		# create a draft expense without an amount for manual completion.
		if getattr(self, 'reminder_only', False) or getattr(self, 'is_flexible', False):
			note = (self.note or '') + (' (Reminder)' if getattr(self, 'reminder_only', False) else ' (Planned)')
			# include payee/recipient information when creating reminder
			expense_kwargs = {'date': self.next_date, 'amount': None, 'category': self.category, 'note': note, 'status': 'draft', 'created_by': user}
			# append To: recipient if provided
			try:
				recipient = (self.payee_recipient or '').strip()
				if recipient:
					base = expense_kwargs.get('note', '').strip()
					if base:
						expense_kwargs['note'] = base + '\nTo: ' + recipient
					else:
						expense_kwargs['note'] = 'To: ' + recipient
				# set payee on expense to month if present else payee field
				expense_payee = (self.payee_month or self.payee or '')
				if expense_payee:
					expense_kwargs['payee'] = expense_payee
			except Exception:
				pass
			return _Expense.objects.create(**expense_kwargs)
		# normal (non-flexible) creation: include payee/recipient if available
		expense_kwargs = {
			'date': self.next_date,
			'amount': self.amount,
			'category': self.category,
			'note': self.note,
			'status': 'posted',
			'created_by': user,
		}
		try:
			recipient = (self.payee_recipient or '').strip()
			if recipient:
				base = (expense_kwargs.get('note') or '').strip()
				if base:
					expense_kwargs['note'] = base + '\nTo: ' + recipient
				else:
					expense_kwargs['note'] = 'To: ' + recipient
			# set payee to month if provided else payee field
			expense_payee = (self.payee_month or self.payee or '')
			if expense_payee:
				expense_kwargs['payee'] = expense_payee
		except Exception:
			pass
		return _Expense.objects.create(**expense_kwargs)
