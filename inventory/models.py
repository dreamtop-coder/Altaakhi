
# Create your models here.

from django.db import models
from services.models import Department

class Supplier(models.Model):
	# optional external/reference code to allow manual IDs (e.g. supplier number)
	supplier_code = models.CharField(max_length=50, blank=True, null=True, unique=True)
	name = models.CharField(max_length=100)
	phone = models.CharField(max_length=20, blank=True, null=True)
	email = models.EmailField(blank=True, null=True)
	address = models.CharField(max_length=255, blank=True, null=True)
	amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

	def __str__(self):
		return self.name

class Part(models.Model):
	name = models.CharField(max_length=100)
	code = models.CharField(max_length=50, blank=True, null=True, unique=True)
	quantity = models.PositiveIntegerField(default=0)
	department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='parts')
	supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='parts')
	low_stock_alert = models.PositiveIntegerField(default=5)
	purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	sale_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	# Flags to control inventory behavior
	track_stock = models.BooleanField(default=False, help_text='If true, selling this part will decrement stock quantity')
	is_purchase = models.BooleanField(default=True, help_text='If true, this part can be purchased from suppliers')
	is_sale = models.BooleanField(default=True, help_text='If true, this part can be sold to customers')

	class Meta:
		ordering = ['code', 'name']

	def __str__(self):
		return self.name
    
