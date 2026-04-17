import os
import sys
from datetime import date

# Django setup
proj_root = os.getcwd()
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()

from invoices.models import RecurringExpense

# Usage: python reset_next_date.py [id|name]
arg = sys.argv[1] if len(sys.argv) > 1 else None
qs = None
if arg:
    if arg.isdigit():
        qs = RecurringExpense.objects.filter(id=int(arg))
    else:
        qs = RecurringExpense.objects.filter(name=arg)
else:
    qs = RecurringExpense.objects.filter(name='راتب فني')

if not qs.exists():
    print('No matching RecurringExpense found for:', arg or 'راتب فني')
    sys.exit(1)

for r in qs:
    old = r.next_date
    r.next_date = date.today()
    r.save()
    print(f"Updated RecurringExpense id={r.id} name='{r.name}' next_date: {old} -> {r.next_date}")
