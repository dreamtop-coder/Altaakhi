# Create your models here.

from django.db import models


class WorkshopSettings(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to="logos/", blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    currency = models.CharField(max_length=10, default="SAR")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    language = models.CharField(max_length=10, default="ar")
    theme = models.CharField(max_length=20, default="light")
    backup_enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.name
