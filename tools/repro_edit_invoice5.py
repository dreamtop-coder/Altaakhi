# Repro edit/delete/replace on invoice id 5
import json
import uuid
from django.test import Client as TestClient
from django.contrib.auth import get_user_model
from invoices.models import Invoice, InvoiceItem
from services.models import Service
from django.utils import timezone
import os

invoice_id = 5
print('Starting edit-repro for invoice', invoice_id)
try:
    inv = Invoice.objects.get(id=invoice_id)
except Exception as e:
    print('Invoice not found:', e)
    raise SystemExit

items = list(InvoiceItem.objects.filter(invoice=inv).order_by('id'))
print('Current items:')
for it in items:
    print(' -', it.id, repr(it.description), float(it.quantity), float(it.rate), float(it.total))

# Ensure a test user exists and is usable
User = get_user_model()
user, _ = User.objects.get_or_create(username='repro_user', defaults={'email': 'repro@local'})
try:
    user.set_password('pw')
    user.save()
except Exception:
    pass

# Build payload:
# - Update first item qty -> *2 (if exists)
# - Omit second item (delete)
# - Add a new service line
items_payload = []
if items:
    first = items[0]
    items_payload.append({
        'invoice_item_id': first.id,
        'description': first.description or '',
        'qty': float((first.quantity or 1) * 2),
        'rate': float(first.rate or 0),
        'disc': float(first.discount or 0),
    })

svc, _ = Service.objects.get_or_create(name='REPRO_SERVICE_B', defaults={'default_price': 15.0, 'department_id': 1})
items_payload.append({
    'description': svc.name,
    'service_id': svc.id,
    'qty': 1,
    'rate': float(svc.default_price or 15.0),
    'disc': 0,
})

print('\nPosting payload:')
print(json.dumps(items_payload, indent=2))

tc = TestClient()
try:
    tc.force_login(user)
except Exception:
    pass
post_data = {'items_json': json.dumps(items_payload), 'amount': '', 'discount': '', 'created_at': ''}
resp = tc.post(f'/invoices/edit/{invoice_id}/', data=post_data)
print('\nPOST response status_code:', resp.status_code)

# reload invoice items
items_after = list(InvoiceItem.objects.filter(invoice=inv).order_by('id'))
print('\nInvoice items after POST:')
for it in items_after:
    print(' -', it.id, repr(it.description), float(it.quantity), float(it.rate), float(it.total))

# tail debug log
log_path = os.path.join(os.getcwd(), 'debug_items_processed.log')
print('\n== debug_items_processed.log tail ==')
if os.path.exists(log_path):
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for ln in lines[-200:]:
            print(ln.strip())
else:
    print('Log file not found at', log_path)

print('\nEdit repro complete')
