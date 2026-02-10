from django.db import models

# Create your models here.



class Client(models.Model):
    STATUS_CHOICES = [
        ("active", "نشط"),
        ("inactive", "معطل"),
    ]
    COMM_PREF_CHOICES = [
        ("email", "البريد الإلكتروني"),
        ("phone", "الهاتف"),
        ("sms", "رسائل قصيرة"),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    customer_id = models.CharField(max_length=30, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")
    notes = models.TextField(blank=True, null=True)
    communication_preference = models.CharField(
        max_length=10, choices=COMM_PREF_CHOICES, default="phone"
    )
    birth_date = models.DateField(blank=True, null=True)
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="added_clients",
    )
    created_at = models.DateTimeField("تاريخ الإضافة", null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
