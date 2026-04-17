from invoices.models import Invoice
nums = ['INV-000073','INV-000072','INV-000071','INV-000070','INV-000069']
qs = Invoice.objects.filter(invoice_number__in=nums)
print('Found now:', qs.count())
for inv in qs:
    print(inv.invoice_number, inv.id, inv.amount, inv.paid)
