from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("DELETE_CLIENT", "Delete Client"),
        ("DELETE_INVOICE", "Delete Invoice"),
        ("DELETE_PAYMENT", "Delete Payment"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    action = models.CharField(max_length=40, choices=ACTION_CHOICES)
    object_type = models.CharField(max_length=80)
    object_id = models.CharField(max_length=64)
    description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.action} {self.object_type}:{self.object_id} by {self.user}"