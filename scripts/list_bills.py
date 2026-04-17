import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import django
django.setup()
from bills.models import Bill

bills = Bill.objects.all().order_by('id')
print('Total bills:', bills.count())
for b in bills:
    print('ID:', b.id, 'number:', b.bill_number, 'status:', b.status, 'grand_total:', b.grand_total, 'date:', getattr(b,'bill_date',None))
