# Create your models here.

from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Service(models.Model):
    STATUS_CHOICES = [
        ("pending", "قيد التنفيذ"),
        ("completed", "مكتملة"),
        ("paid", "مدفوعة"),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    default_price = models.DecimalField(max_digits=10, decimal_places=2)
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="services"
    )
    car = models.ForeignKey(
        "cars.Car",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="services",
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parts = models.ManyToManyField(
        'inventory.Part', blank=True, related_name='services'
    )

    def __str__(self):
        return self.name
