import os
import json

# bootstrap Django so this script can run stand-alone
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()

from inventory.models import Part
from bills.models import Bill

def dump(q):
    try:
        return json.dumps(list(q), ensure_ascii=False)
    except Exception:
        return str(list(q))

try:
    print('Parts Turbo:', dump(Part.objects.filter(name__icontains='Turbo').values('id','name','purchase_price','quantity')))
except Exception as e:
    print('Parts Turbo: error', e)
try:
    print('Parts Cylinder Head:', dump(Part.objects.filter(name__icontains='Cylinder Head').values('id','name','purchase_price','quantity')))
except Exception as e:
    print('Parts Cylinder Head: error', e)
print('BIL-000003 exists:', Bill.objects.filter(bill_number='BIL-000003').exists())
print('Recent bills (last 20):', dump(Bill.objects.all().order_by('-id').values('id','bill_number','supplier_id','grand_total')[:20]))

# also print lines for bills 7,8,9 if present
for bid in [7,8,9]:
    b = Bill.objects.filter(id=bid).first()
    if b:
        try:
            print(f'Bill {bid} lines:', dump(list(b.lines.values('description','quantity','rate','amount'))))
        except Exception as e:
            print(f'Bill {bid} lines: error', e)
    else:
        print(f'Bill {bid}: not found')
