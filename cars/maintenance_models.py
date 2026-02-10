from django.db import models
from .models import Car
from services.models import Service


from invoices.models import Invoice


class MaintenanceRecord(models.Model):
    delivery_date = models.DateTimeField(
        blank=True, null=True, verbose_name="تاريخ تسليم المركبة"
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="maintenance_records",
        verbose_name="رقم الفاتورة",
    )
    car = models.ForeignKey(
        Car, on_delete=models.CASCADE, related_name="maintenance_records"
    )
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()
    ready_at = models.DateTimeField(
        blank=True, null=True, verbose_name="تاريخ انتهاء التصليح"
    )
    is_finished = models.BooleanField(
        default=False, verbose_name="تم الانتهاء من الصيانة"
    )

    def get_status(self):
        if self.ready_at and not self.is_finished:
            return "جاهزة للاستلام"
        elif self.is_finished:
            return "تم التسليم"
        else:
            return "قيد الإصلاح"

    def __str__(self):
        return f"{self.car.plate_number} - {self.service.name} ({self.price} ريال)"
