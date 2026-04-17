import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()

from bills.models import Bill, BillPayment
from inventory.models import Supplier
from django.db.models import Sum

def inspect(supplier_name=None, bill_number=None):
    if supplier_name:
        try:
            s = Supplier.objects.filter(name__icontains=supplier_name).first()
            if not s:
                print('Supplier not found for name containing:', supplier_name)
            else:
                print('Supplier:', s.id, s.name, 'amount=', s.amount)
        except Exception as e:
            print('Error fetching supplier:', e)
    if bill_number:
        try:
            b = Bill.objects.filter(bill_number=bill_number).select_related('supplier').first()
            if not b:
                print('Bill not found with number:', bill_number)
            else:
                print('Bill:', b.id, b.bill_number, 'supplier=', getattr(b.supplier, 'name', None), 'status=', b.status, 'grand_total=', b.grand_total)
                paid = BillPayment.objects.filter(bill=b, status='paid').aggregate(total=Sum('amount'))['total'] or 0
                print('Sum of paid BillPayments for this bill =', paid)
        except Exception as e:
            print('Error fetching bill:', e)

if __name__ == '__main__':
    inspect(supplier_name='Busanad Steel And Aluminium', bill_number='BIL-000001')
