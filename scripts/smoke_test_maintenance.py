import os
import django
import json
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
django.setup()

from django.test import Client
from clients.models import Client as Cl
from services.models import Service
from invoices.models import Invoice, InvoiceItem

client = Client()

cli = Cl.objects.first() or Cl.objects.create(first_name='Test', last_name='Client')
svc = Service.objects.first() or Service.objects.create(name='Test Service', default_price=10)

data = {
    'client': str(cli.pk),
    'service': str(svc.pk),
    'price': '10',
    'maintenance_date': '2026-02-19',
    'plate_number': 'TEST123',
    'items_json': json.dumps([
        {'description': 'Item A', 'qty': 1, 'rate': 10.0, 'discount': 0.0, 'total': 10.0}
    ])
}

print('Posting data:', data)
resp = client.post('/maintenance/add/', data, follow=True, HTTP_HOST='127.0.0.1')
print('Response status:', resp.status_code)
print('Redirect chain:', resp.redirect_chain)

print('Invoice count:', Invoice.objects.count())
inv = Invoice.objects.order_by('-id').first()
if inv:
    print('Last invoice:', inv.invoice_number, 'amount=', inv.amount)
    print('InvoiceItem count for last invoice:', InvoiceItem.objects.filter(invoice=inv).count())
    for it in InvoiceItem.objects.filter(invoice=inv):
        print(' -', it.description, it.quantity, it.rate, it.discount, it.total)
else:
    print('No invoice found')

sys.stdout.flush()
