import os
import sys
import django
from decimal import Decimal
from datetime import date

# ensure project root is on PYTHONPATH
proj_root = os.getcwd()
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
django.setup()

from invoices.models import ExpenseCategory, RecurringExpense

# Create or get category
cat, created = ExpenseCategory.objects.get_or_create(name='Salaries', defaults={'description': 'Monthly salaries'})
print('Category:', cat.id, cat.name, 'created=', created)

# Create recurring entry
today = date.today()
rec, created = RecurringExpense.objects.get_or_create(
    name='راتب فني',
    defaults={
        'amount': Decimal('300.00'),
        'category': cat,
        'frequency': 'monthly',
        'interval': 1,
        'start_date': today,
        'next_date': today,
        'active': True,
        'note': 'راتب فني',
    }
)
print('Recurring:', rec.id if rec else None, 'created=', created)
