
# Create your models here.
from django.db import models

from clients.models import Client
from .brand_models import CarBrand, CarModel


class Service(models.Model):
	name = models.CharField(max_length=100, unique=True, verbose_name="اسم الخدمة الفنية")
	sale_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="سعر الخدمة", default=0)

	def __str__(self):
		return self.name


class Car(models.Model):
	def save(self, *args, **kwargs):
		# إذا تغير العميل المرتبط بالسيارة، اعتبرها مباعة
		if self.pk:
			old = Car.objects.get(pk=self.pk)
			if old.client_id != self.client_id:
				# إذا كان هناك عميل جديد، السيارة تعود نشطة
				if self.client_id:
					self.status = 'waiting'
				else:
					self.status = 'done'
		super().save(*args, **kwargs)
	STATUS_CHOICES = [
		('waiting', 'قيد الانتظار'),
		('in_progress', 'جاري التنفيذ'),
		('pending_payment', 'معلقة للدفع'),
		('paid_waiting_collection', 'مدفوعة - بانتظار الاستلام'),
		('done', 'مُنتهية'),
		# legacy values for compatibility
		('active', 'نشطة'),
		('ready', 'بانتظار التسليم'),
		('sold', 'مباعة'),
	]
	FUEL_CHOICES = [
		('gasoline', 'بنزين'),
		('diesel', 'ديزل'),
		('electric', 'كهرباء'),
		('hybrid', 'هايبرد'),
	]

	client = models.ForeignKey('clients.Client', on_delete=models.CASCADE, related_name='cars')
	plate_number = models.CharField(max_length=20, unique=True)
	brand = models.ForeignKey(CarBrand, on_delete=models.SET_NULL, null=True, blank=True, related_name='cars')
	model = models.ForeignKey(CarModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='cars')
	year = models.PositiveIntegerField(blank=True, null=True)
	color = models.CharField(max_length=30, blank=True, null=True)
	fuel_type = models.CharField(max_length=10, choices=FUEL_CHOICES, default='gasoline')
	vin_number = models.CharField(max_length=30, unique=True, blank=True, null=True)
	status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='waiting')
	notes = models.TextField(blank=True, null=True)
	entry_date = models.DateTimeField(blank=True, null=True, verbose_name='تاريخ دخول الورشة')
	last_visit = models.DateTimeField(blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		if self.brand and self.model:
			return f"{self.plate_number} - {self.brand.name} {self.model.name}"
		return f"{self.plate_number}"

	@property
	def unpaid_invoice_id(self):
		unpaid_invoice = self.invoices.filter(paid=False).first()
		return unpaid_invoice.id if unpaid_invoice else None

	def is_in_workshop(self):
		"""Return True when there is an open (unfinished & not delivered)
		maintenance record for this car.
		This centralizes the workshop membership logic to avoid repeating
		queries across views and templates.
		"""
		try:
			from .maintenance_models import MaintenanceRecord
			return MaintenanceRecord.objects.filter(car=self, is_finished=False, delivery_date__isnull=True).exists()
		except Exception:
			return False

	def get_current_record(self):
		"""Return the current open MaintenanceRecord for this car, if any.
		Prefers the most recently created unfinished record.
		"""
		try:
			from .maintenance_models import MaintenanceRecord
			return MaintenanceRecord.objects.filter(car=self, is_finished=False, delivery_date__isnull=True).order_by('-created_at', '-id').first()
		except Exception:
			return None
