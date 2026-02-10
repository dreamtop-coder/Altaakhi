from django.db import models


from cars.models import Car
from clients.models import Client


class Booking(models.Model):
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="bookings", null=True, blank=True
    )
    car = models.ForeignKey(
        Car, on_delete=models.CASCADE, related_name="bookings", null=True, blank=True
    )
    plate_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="رقم السيارة (اختياري)",
    )
    phone = models.CharField(max_length=20)
    service_type = models.CharField(max_length=100)
    service_date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        default="pending",
        db_index=True,
        help_text="حالة الحجز: pending, confirmed, cancelled",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.phone} - {self.service_type} - {self.service_date}"
