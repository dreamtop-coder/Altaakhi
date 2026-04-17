from django.db.models import Sum
from invoices.models import Invoice, InvoiceItem
from bills.models import Bill
import decimal

print('--- Financial debug ---')
try:
    total_revenue = Invoice.objects.aggregate(total=Sum('amount'))['total'] or 0
    print('total_revenue:', total_revenue)
except Exception as e:
    print('total_revenue: ERROR', e)

# compute COGS using find_part_for_description (same logic as view)
try:
    from inventory.utils import find_part_for_description
    cogs = decimal.Decimal('0')
    items_qs = InvoiceItem.objects.filter(invoice__in=Invoice.objects.all()).values('description', 'quantity')
    sample_missing = []
    for it in items_qs:
        desc = (it.get('description') or '').strip()
        try:
            qty = decimal.Decimal(str(it.get('quantity') or 0))
        except Exception:
            qty = decimal.Decimal('0')
        if not desc or qty == 0:
            continue
        try:
            part = find_part_for_description(desc)
        except Exception:
            part = None
        if part and getattr(part, 'purchase_price', None) is not None:
            try:
                cogs += (qty * decimal.Decimal(str(part.purchase_price)))
            except Exception:
                pass
        else:
            sample_missing.append(desc)
    print('cogs:', cogs)
    if sample_missing:
        print('sample unmatched descriptions (first 10):', sample_missing[:10])
except Exception as e:
    print('cogs: ERROR', e)

try:
    total_expenses = Bill.objects.aggregate(total=Sum('grand_total'))['total'] or 0
    print('total_expenses:', total_expenses)
except Exception as e:
    print('total_expenses: ERROR', e)

print('--- end ---')
