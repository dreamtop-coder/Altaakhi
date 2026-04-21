# Repro: POST three identical service rows to edit_invoice and report results
import json
import uuid
from django.test import Client as TestClient
from django.contrib.auth import get_user_model
from django.utils import timezone

from clients.models import Client as ClientModel
from invoices.models import Invoice, InvoiceItem
from services.models import Service

print('Starting repro: three identical service rows')

# create or reuse test client
client_obj, _ = ClientModel.objects.get_or_create(first_name='ReproClient', defaults={'phone_number': '000000', 'customer_id': 'REPRO-CLIENT-1'})
# create service
service, _ = Service.objects.get_or_create(name='REPRO_SERVICE_A', defaults={'default_price': 10.0, 'department_id': 1})

# create invoice
inv = Invoice.objects.create(invoice_number=f'INV-REPRO-{int(timezone.now().timestamp())}', client=client_obj, amount=0.0, paid=False, created_at=timezone.now())
print('Created invoice id:', inv.id)

# create test user
User = get_user_model()
user, _ = User.objects.get_or_create(username='repro_user', defaults={'email': 'repro@local', 'password': 'pw'})

# prepare items_json: three entries same service, each with unique client_row_id
items = []
for i in range(3):
    items.append({
        'description': service.name,
        'service_id': service.id,
        'qty': 1,
        'rate': float(service.default_price),
        'disc': 0,
        'client_row_id': str(uuid.uuid4())
    })

tc = TestClient()
# force login (ensure user has usable password)
try:
    user.set_password('pw')
    user.save()
except Exception:
    pass
tc.force_login(user)

post_data = {'items_json': json.dumps(items), 'amount': '', 'discount': '', 'created_at': ''}
resp = tc.post(f'/invoices/edit/{inv.id}/', data=post_data)
print('POST response status_code:', resp.status_code)

# reload invoice items
items_after = list(InvoiceItem.objects.filter(invoice=inv).values('id','description','quantity','rate','discount','total'))
print('Invoice items count after POST:', len(items_after))
for it in items_after:
    print(' -', it)

# tail debug log
import os
log_path = os.path.join(os.getcwd(), 'debug_items_processed.log')
print('\n== debug_items_processed.log tail ==')
if os.path.exists(log_path):
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for ln in lines[-200:]:
            print(ln.strip())
else:
    print('Log file not found at', log_path)

print('\nRepro script complete')
