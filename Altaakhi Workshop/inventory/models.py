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
    supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL, null=True, related_name="parts"
    )
    low_stock_alert = models.PositiveIntegerField(default=5)

    def __str__(self):
        return self.name
