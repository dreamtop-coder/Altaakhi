import os
import django
from decimal import Decimal, ROUND_HALF_UP

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
django.setup()

from inventory.models import Part
from bills.models import BillLine

changes = []
for part in Part.objects.all():
    try:
        qs = BillLine.objects.filter(part_id=part.id)
        total = Decimal('0')
        for ln in qs:
            try:
                total += Decimal(str(ln.quantity or 0))
            except Exception:
                total += Decimal('0')
        # round to integer like other code
        expected = int(total.to_integral_value(rounding=ROUND_HALF_UP))
        current = int(part.quantity or 0)
        if expected != current:
            changes.append((part.id, part.name, current, expected))
    except Exception as e:
        print('error for part', part.id, e)

if not changes:
    print('No discrepancies found. All Part.quantity values match BillLines totals.')
else:
    print('Discrepancies found:')
    for pid, name, cur, exp in changes:
        print(f'Part {pid} - {name}: current={cur}, expected={exp}')
    print('\nThis is a dry-run. To apply fixes, re-run with environment variable APPLY=1')
    if os.environ.get('APPLY') == '1':
        from django.db import transaction
        with transaction.atomic():
            for pid, name, cur, exp in changes:
                p = Part.objects.get(pk=pid)
                p.quantity = exp
                p.save()
                print(f'Updated Part {pid} - {name}: {cur} -> {exp}')
        print('Applied changes.')
