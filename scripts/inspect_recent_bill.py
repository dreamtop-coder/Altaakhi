import os
import django
import sys
# ensure project root is on PYTHONPATH so 'workshop' package imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
django.setup()
from bills.models import Bill, BillLine
from decimal import Decimal

print('Inspecting last 5 Bills and their lines')
for b in Bill.objects.order_by('-id')[:5]:
    print('---')
    print('Bill id:', b.id, 'number:', b.bill_number, 'grand_total:', b.grand_total, 'status:', b.status)
    for ln in b.lines.all():
        print('  Line id:', ln.id, 'desc:', ln.description, 'qty:', ln.quantity, 'rate:', ln.rate, 'amount:', ln.amount, 'account_type:', ln.account_type)

# Also print any recent session bills in a short form is not possible from here, but DB persistent Bills are shown.
