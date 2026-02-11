# Create your models here.

from django.db import models
from services.models import Department


class Supplier(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name


class Part(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=0)
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, related_name="parts"
    )
    # whether this part is a real stock item (purchases affect quantity).
    # Services and non-stock entries should set this to False.
    is_stock_item = models.BooleanField(default=True)
    suppliers = models.ManyToManyField(
        Supplier, blank=True, related_name="parts"
    )
    low_stock_alert = models.PositiveIntegerField(default=5)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    sale_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name


class Purchase(models.Model):
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name="purchases"
    )
    invoice_number = models.CharField(max_length=50, blank=True, null=True)
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_return = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.supplier.name} - {self.amount} on {self.date}"


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    part = models.ForeignKey(Part, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_items')
    part_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=14, decimal_places=2)

    def __str__(self):
        return f"{self.part_name} x{self.quantity} - {self.total_price}"
