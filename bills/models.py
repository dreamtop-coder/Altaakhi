from django.db import models


class Bill(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    )

    bill_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey('inventory.Supplier', on_delete=models.SET_NULL, null=True, blank=True, related_name='bills')
    bill_date = models.DateField()
    notes = models.TextField(blank=True)

    subtotal = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    discount_total = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    grand_total = models.DecimalField(max_digits=14, decimal_places=3, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-bill_date', '-created_at']

    def __str__(self):
        return f"{self.bill_number} - {self.supplier.name if self.supplier else 'Unknown'}"


class BillLine(models.Model):
    bill = models.ForeignKey(Bill, related_name='lines', on_delete=models.CASCADE)
    part = models.ForeignKey('inventory.Part', on_delete=models.SET_NULL, null=True, blank=True, related_name='bill_lines')
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    rate = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    # Account type: controls whether this purchase line is inventory (COGS) or an expense
    ACCOUNT_CHOICES = (
        ('inventory', 'Inventory'),
        ('expense', 'Expense'),
    )
    account_type = models.CharField(max_length=16, choices=ACCOUNT_CHOICES, default='inventory', help_text='If Expense, treat this line as an operational expense rather than inventory/COGS')

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.description} ({self.quantity} x {self.rate})"


class BillPayment(models.Model):
    STATUS_CHOICES = (
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
        ('partial', 'Partial'),
    )
    METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('bank', 'Bank Transfer'),
        ('other', 'Other'),
    )

    bill = models.ForeignKey(Bill, related_name='payments', on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey('inventory.Supplier', related_name='payments', on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    payment_date = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='cash')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='paid')
    reference = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.amount} - {self.supplier.name if self.supplier else 'Unknown'} - {self.payment_date}"
