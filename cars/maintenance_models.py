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
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
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
        svc_name = self.service.name if self.service else "قطع/بدون خدمة"
        return f"{self.car.plate_number} - {svc_name} ({self.price} ريال)"


class MaintenancePart(models.Model):
    maintenance = models.ForeignKey(
        MaintenanceRecord, on_delete=models.CASCADE, related_name='parts'
    )
    part = models.ForeignKey(
        'inventory.Part', on_delete=models.SET_NULL, null=True, blank=True
    )
    part_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.part_name} x{self.quantity} - {self.total_price}"
