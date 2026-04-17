import django, os, sys
# ensure project root on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','workshop.settings')
django.setup()
from django.db.models import Sum
from invoices.models import Invoice, InvoiceItem
from bills.models import BillLine
from inventory.utils import find_part_for_description
from inventory.models import Part
from decimal import Decimal

qs = Invoice.objects.all()
total_revenue = qs.aggregate(total=Sum('amount'))['total'] or 0
collected = qs.filter(paid=True).aggregate(total=Sum('amount'))['total'] or 0
outstanding = qs.filter(paid=False).aggregate(total=Sum('amount'))['total'] or 0

# compute cogs and invoice-line expenses similar to view
cogs_total = Decimal('0')
invoice_line_expenses = Decimal('0')
items_qs = InvoiceItem.objects.all().values('description','quantity','rate','total','invoice')
for it in items_qs:
    desc = (it.get('description') or '').strip()
    try:
        qty = Decimal(str(it.get('quantity') or 0))
    except Exception:
        qty = Decimal('0')
    if not desc or qty == 0:
        continue
    part = None
    try:
        part = find_part_for_description(desc)
    except Exception:
        part = None
    # determine line_total
    line_total = None
    try:
        if it.get('total') is not None:
            line_total = Decimal(str(it.get('total')))
        else:
            line_total = qty * Decimal(str(it.get('rate') or 0))
    except Exception:
        line_total = None
    # determine priority: BillLine.account_type
    line_is_inventory = None
    try:
        if part:
            last_purchase_line = BillLine.objects.filter(part=part).select_related('bill').order_by('-bill__bill_date','-bill__created_at').first()
            if last_purchase_line and getattr(last_purchase_line,'account_type',None):
                line_is_inventory = (last_purchase_line.account_type == 'inventory')
    except Exception:
        line_is_inventory = None
    try:
        if line_is_inventory is None and part:
            line_is_inventory = bool(getattr(part,'is_inventory', True))
    except Exception:
        line_is_inventory = None
    # accumulate
    try:
        if line_is_inventory is True and part and getattr(part,'purchase_price',None) is not None:
            cogs_total += qty * Decimal(str(part.purchase_price))
        elif line_is_inventory is False:
            if line_total is not None:
                invoice_line_expenses += line_total
        else:
            if part and getattr(part,'purchase_price',None) is not None:
                cogs_total += qty * Decimal(str(part.purchase_price))
            else:
                if line_total is not None:
                    cogs_total += line_total
    except Exception:
        pass

from bills.models import Bill
bill_qs = Bill.objects.all()
try:
    total_expenses = bill_qs.aggregate(total=Sum('grand_total'))['total'] or 0
except Exception:
    total_expenses = 0
# include invoice-line expenses
try:
    total_expenses = (total_expenses or 0) + invoice_line_expenses
except Exception:
    pass

from decimal import Decimal
try:
    gross_profit = Decimal(str(total_revenue or 0)) - Decimal(str(cogs_total))
    net_profit = gross_profit - Decimal(str(total_expenses or 0))
except Exception:
    gross_profit = Decimal('0')
    net_profit = Decimal('0')

print('total_revenue:', total_revenue)
print('collected:', collected)
print('outstanding:', outstanding)
print('cogs_total:', cogs_total)
print('invoice_line_expenses:', invoice_line_expenses)
print('total_expenses (bills + invoice-line expenses):', total_expenses)
print('gross_profit:', gross_profit)
print('net_profit:', net_profit)
