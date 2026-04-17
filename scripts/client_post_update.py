import os
import sys
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
django.setup()

from django.test import Client
from bills.models import Bill

BILL_ID = 7
c = Client(enforce_csrf_checks=False)

bill = Bill.objects.filter(pk=BILL_ID).first()
if not bill:
    print('BILL_NOT_FOUND')
    sys.exit(2)

items = []
for ln in bill.lines.all():
    acct = ln.account_type or 'inventory'
    new_acct = 'inventory' if acct == 'expense' else acct
    items.append({
        'description': ln.description,
        'qty': float(ln.quantity or 0),
        'rate': float(ln.rate or 0),
        'discount': float(ln.discount_percent or 0),
        'account_type': new_acct,
        'amount': float(ln.amount or 0),
    })

payload = {
    'bill_id': str(BILL_ID),
    'bill_number': bill.bill_number or '',
    'bill_date': bill.bill_date.isoformat() if bill.bill_date else '',
    'selected_supplier_id': str(bill.supplier.id) if bill.supplier else '',
    'notes': bill.notes or '',
    'items_json': json.dumps(items),
    'client_grand_total': str(bill.grand_total or 0),
    'action': 'save',
}

print('Client posting payload:', payload)
resp = c.post('/bills/add/', data=payload)
print('Response status', resp.status_code)
print('Response redirect chain:', resp._headers.get('location') if hasattr(resp,'_headers') else None)

bill.refresh_from_db()
for ln in bill.lines.all():
    print('LINE', ln.id, ln.description, ln.account_type)

print('DONE')
