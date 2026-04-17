import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','workshop.settings_test')
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import django
django.setup()

import json
from django.test import Client
from invoices.models import Invoice
from inventory.models import Part
from django.contrib.auth import get_user_model

c = Client()
User = get_user_model()
user, _ = User.objects.get_or_create(username='test_auto')
user.set_password('test')
user.save()
c.force_login(user)
inv = Invoice.objects.filter(invoice_number='INV-AJAX-TEST').first()
if not inv:
    print('Invoice not found')
    raise SystemExit(1)
part = Part.objects.filter(name__iexact='Turbo').first()
print('Inv id', inv.id, 'Part id', part.id if part else None, 'Part qty', getattr(part,'quantity',None))
items = [{'part_id': part.id, 'description': part.name, 'qty': 10, 'rate': 10, 'disc': 0}]
post = {'items_json': json.dumps(items), 'amount': '100'}
resp = c.post(f'/invoices/edit/{inv.id}/', post, follow=True, HTTP_HOST='127.0.0.1')
print('Status', resp.status_code)
print('Messages in content contains Arabic shortage?', 'الكمية غير متوفرة' in resp.content.decode(errors='ignore'))
print('InvoiceItem count for invoice after:', inv.items.count())
print('Part qty after:', getattr(part,'quantity',None))
