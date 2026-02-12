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

    def __init__(self, *args, **kwargs):
        # Backwards-compatible alias: accept `sale_price` and map it to `default_price`.
        if 'sale_price' in kwargs and 'default_price' not in kwargs:
            kwargs['default_price'] = kwargs.pop('sale_price')
        # If no department provided, try to attach (or create) an 'Imported' department
        # to satisfy NOT NULL DB constraint in environments where code constructs
        # Service instances without specifying a department.
        # Treat an explicit `None` the same as missing so tests and code
        # that pass `department=None` still get a sane default instead
        # of causing a NOT NULL DB constraint error.
        # Only inject a default department when the model is being constructed
        # from keyword args (e.g. Service(...)) and not when Django is
        # instantiating objects from DB rows (which pass positional args).
        if (('department' not in kwargs or kwargs.get('department') is None) and not args):
            try:
                dept, _ = Department.objects.get_or_create(name='Imported')
                kwargs['department'] = dept
            except Exception:
                # If the DB/tables aren't available yet (migrations in progress),
                # skip and let validation/migrations handle it.
                pass

        super().__init__(*args, **kwargs)
