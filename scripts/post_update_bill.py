import os
import sys
import json
import django
import requests
from decimal import Decimal

# Setup Django env
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
django.setup()

from bills.models import Bill, BillLine
from inventory.models import Supplier

BILL_ID = 7
BASE = 'http://127.0.0.1:8000'
EDIT_URL = f'{BASE}/bills/edit/{BILL_ID}/'
POST_URL = f'{BASE}/bills/add/'

# Build items payload from DB, toggling account_type to 'inventory' if currently 'expense'
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

s = requests.Session()
# GET edit page to fetch CSRF token cookie and hidden input
r = s.get(EDIT_URL, timeout=10)
if r.status_code != 200:
    print('GET_FAILED', r.status_code)
    sys.exit(3)

# try to extract csrf token value from hidden input
import re
m = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text)
if not m:
    # try single quotes
    m = re.search(r"name='csrfmiddlewaretoken' value='([^']+)'", r.text)
if not m:
    # fallback to cookie
    csrf = s.cookies.get('csrftoken') or s.cookies.get('csrf') or ''
else:
    csrf = m.group(1)

payload = {
    'bill_id': str(BILL_ID),
    'bill_number': bill.bill_number or '',
    'bill_date': bill.bill_date.isoformat() if bill.bill_date else '',
    'selected_supplier_id': str(bill.supplier.id) if bill.supplier else '',
    'notes': bill.notes or '',
    'items_json': json.dumps(items),
    'debug_update': '1',
    'client_grand_total': str(bill.grand_total or 0),
    'action': 'save',
}

headers = {
    'Referer': EDIT_URL,
    'X-CSRFToken': csrf,
}

print('Posting update with items:', items)
post = s.post(POST_URL, data=payload, headers=headers, timeout=20)
print('POST status', post.status_code)
try:
    print('POST final URL:', post.url)
    print('POST history:', [ (r.status_code, r.headers.get('Location')) for r in post.history ])
    print('POST response snippet:\n', post.text[:800])
except Exception:
    pass
if post.status_code not in (200,302):
    print('POST_FAILED_BODY', post.text[:400])

# Refresh DB and show lines
bill.refresh_from_db()
for ln in bill.lines.all():
    print('LINE', ln.id, ln.description, ln.account_type)

# exit 0
print('DONE')
