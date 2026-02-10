# Create your models here.

from django.db import models


class Report(models.Model):
    REPORT_TYPES = [
        ("sales", "مبيعات"),
        ("clients", "العملاء الأكثر نشاطاً"),
        ("parts", "القطع الأكثر استخداماً"),
        ("finance", "التقرير المالي"),
    ]
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    period_start = models.DateField()
    period_end = models.DateField()
    generated_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField()

    def __str__(self):
        return f"{self.get_report_type_display()} ({self.period_start} - {self.period_end})"
