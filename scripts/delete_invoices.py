# Backup and delete specific test invoices
from invoices.models import Invoice
from django.core import serializers

nums = ['INV-000073','INV-000072','INV-000071','INV-000070','INV-000069']
qs = Invoice.objects.filter(invoice_number__in=nums)
print('Found invoices to delete:', qs.count())

# backup invoices
try:
    data = serializers.serialize('json', qs)
    open('scripts/invoices_to_delete_backup.json','w',encoding='utf-8').write(data)
    print('Wrote scripts/invoices_to_delete_backup.json')
except Exception as e:
    print('Failed to write invoices backup:', e)

# backup related items and payments
items = []
payments = []
for inv in qs:
    try:
        items.extend(list(inv.items.all()))
    except Exception:
        pass
    try:
        payments.extend(list(inv.payments.all()))
    except Exception:
        pass
if items:
    try:
        open('scripts/invoice_items_backup.json','w',encoding='utf-8').write(serializers.serialize('json', items))
        print('Wrote scripts/invoice_items_backup.json')
    except Exception as e:
        print('Failed to write invoice items backup:', e)
if payments:
    try:
        open('scripts/invoice_payments_backup.json','w',encoding='utf-8').write(serializers.serialize('json', payments))
        print('Wrote scripts/invoice_payments_backup.json')
    except Exception as e:
        print('Failed to write invoice payments backup:', e)

# show details
for inv in qs:
    print('Will delete invoice:', inv.invoice_number, 'id=', inv.id, 'amount=', inv.amount, 'paid=', inv.paid)

# perform delete
if qs.exists():
    count, details = qs.delete()
    print('Delete result - objects deleted count:', count)
    print('Related delete details (per model):', details)
else:
    print('No invoices matched; nothing deleted')
