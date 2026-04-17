import os
import sys
import django
from decimal import Decimal, ROUND_HALF_UP

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
django.setup()

from bills.models import Bill, BillLine
from inventory.models import Part, Supplier

BILL_ID = 7
bill = Bill.objects.filter(pk=BILL_ID).first()
if not bill:
    print('BILL_NOT_FOUND')
    sys.exit(2)

# Build lines payload to simulate incoming data
lines = []
for ln in bill.lines.all():
    lines.append({
        'description': ln.description,
        'qty': ln.quantity,
        'rate': ln.rate,
        'discount': ln.discount_percent,
        'account_type': 'inventory',
        'amount': ln.amount,
    })

print('Simulating update for bill', bill.id, 'with', len(lines), 'lines')

try:
    existing = Bill.objects.select_related('supplier').prefetch_related('lines').get(pk=int(BILL_ID))
    print('Loaded existing bill OK')
except Exception as e:
    print('Failed to load existing bill:', e)
    raise

try:
    # update fields
    existing.bill_number = existing.bill_number
    existing.supplier = existing.supplier
    existing.bill_date = existing.bill_date
    existing.notes = existing.notes
    existing.subtotal = existing.subtotal
    existing.discount_total = existing.discount_total
    existing.grand_total = existing.grand_total
    existing.status = existing.status
    existing.save()
    print('Updated fields saved OK')
except Exception as e:
    print('Failed updating fields:', e)

# revert old part quantities and delete old lines
try:
    for old_ln in existing.lines.all():
        try:
            part = Part.objects.filter(name__iexact=old_ln.description).first()
            if part:
                try:
                    dec_q = Decimal(str(old_ln.quantity or 0))
                    delta = int(dec_q.to_integral_value(rounding=ROUND_HALF_UP))
                except Exception:
                    delta = int(old_ln.quantity or 0)
                part.quantity = (part.quantity or 0) - delta
                if part.quantity < 0:
                    part.quantity = 0
                part.save()
        except Exception as e:
            print('inner revert part error for line', old_ln.id, ':', e)
    existing.lines.all().delete()
    print('Old lines deleted and part quantities reverted OK')
except Exception as e:
    print('Failed reverting old lines:', e)

# create new lines and update parts
try:
    for ln in lines:
        BillLine.objects.create(
            bill=existing,
            description=ln['description'],
            quantity=ln['qty'],
            rate=ln['rate'],
            discount_percent=ln['discount'],
            account_type=ln.get('account_type', 'inventory'),
            amount=ln['amount']
        )
        try:
            part = Part.objects.filter(name__iexact=ln['description']).first()
            if part:
                try:
                    rate_val = Decimal(str(ln['rate']))
                except Exception:
                    rate_val = None
                if rate_val and rate_val != Decimal('0'):
                    part.purchase_price = rate_val
                try:
                    dec_q = Decimal(str(ln['qty'] or 0))
                    add_q = int(dec_q.to_integral_value(rounding=ROUND_HALF_UP))
                except Exception:
                    add_q = int(ln['qty'] or 0)
                part.quantity = (part.quantity or 0) + add_q
                part.save()
        except Exception as e:
            print('inner create part update error for', ln['description'], ':', e)
    print('Created new lines and updated parts OK')
except Exception as e:
    print('Failed creating new lines:', e)

# adjust supplier balances
try:
    supplier = existing.supplier
    action = 'save'
    old_supplier = None
    old_grand = Decimal('0')
    try:
        if old_supplier and action != 'save_draft':
            old_supplier.amount = (old_supplier.amount or Decimal('0')) - (old_grand or Decimal('0'))
            old_supplier.save()
    except Exception as e:
        print('revert old supplier error', e)
    try:
        if supplier and action != 'save_draft':
            supplier.amount = (supplier.amount or Decimal('0')) + existing.grand_total
            supplier.save()
            print('Supplier balance updated OK')
    except Exception as e:
        print('supplier update error', e)
except Exception as e:
    print('Failed adjusting supplier balances:', e)

print('Simulation complete')
