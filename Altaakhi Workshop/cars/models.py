# Create your models here.
from django.db import models

from .brand_models import CarBrand, CarModel


class Service(models.Model):
    name = models.CharField(
        max_length=100, unique=True, verbose_name="اسم الخدمة الفنية"
    )
    sale_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="سعر الخدمة", default=0
    )

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
                    self.status = "active"
                else:
                    self.status = "sold"
        super().save(*args, **kwargs)

    STATUS_CHOICES = [
        ("active", "نشطة"),  # السيارة تحت الصيانة
        ("ready", "بانتظار التسليم"),  # الصيانة انتهت
        ("pending_payment", "معلقة للدفع"),  # بانتظار الدفع
        ("sold", "مباعة"),  # تم التسليم النهائي
    ]
    FUEL_CHOICES = [
        ("gasoline", "بنزين"),
        ("diesel", "ديزل"),
        ("electric", "كهرباء"),
        ("hybrid", "هايبرد"),
    ]

    client = models.ForeignKey(
        "clients.Client", on_delete=models.CASCADE, related_name="cars"
    )
    plate_number = models.CharField(max_length=20, unique=True)
    brand = models.ForeignKey(
        CarBrand, on_delete=models.SET_NULL, null=True, blank=True, related_name="cars"
    )
    model = models.ForeignKey(
        CarModel, on_delete=models.SET_NULL, null=True, blank=True, related_name="cars"
    )
    year = models.PositiveIntegerField(blank=True, null=True)
    color = models.CharField(max_length=30, blank=True, null=True)
    fuel_type = models.CharField(
        max_length=10, choices=FUEL_CHOICES, default="gasoline"
    )
    vin_number = models.CharField(max_length=30, unique=True, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    notes = models.TextField(blank=True, null=True)
    entry_date = models.DateTimeField(
        blank=True, null=True, verbose_name="تاريخ دخول الورشة"
    )
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
