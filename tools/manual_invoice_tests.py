# Manual invoice/bill tests
# Run inside `manage.py shell` so Django settings and apps are ready.
import json
from django.test import Client as TestClient
from django.contrib.auth import get_user_model
from django.utils import timezone

print('Starting manual invoice tests')

# Helper to pretty print a model count
def count(model, **kw):
    try:
        return model.objects.filter(**kw).count()
    except Exception as e:
        return f'ERR: {e}'

# Test A: POST to add_maintenance_record (creates invoice when items_json present)
print('\nTEST A: create via /cars/maintenance/add/ with Part.quantity=0')
from clients.models import Client as ClientModel
from inventory.models import Part
from invoices.models import Invoice, InvoiceItem

# cleanup any prior test objects
ClientModel.objects.filter(customer_id__startswith='TEST-').delete()
Part.objects.filter(code__startswith='TEST-').delete()
Invoice.objects.filter(invoice_number__startswith='INV-TEST').delete()

# create client
client_obj = ClientModel.objects.create(first_name='TestClient', phone_number='000000', customer_id='TEST-CLIENT-1')
# create part with zero quantity
part = Part.objects.create(name='TEST_PART_A', code='TEST-A', quantity=0, track_stock=True, purchase_price=1.0, sale_price=2.0, is_sale=True)

# prepare items_json referencing the part name
items = [{'description': part.name, 'qty': 1, 'rate': float(part.sale_price), 'discount': 0, 'amount': float(part.sale_price)}]

tc = TestClient()
# POST to maintenance add
resp = tc.post('/cars/maintenance/add/', data={'selected_client_id': str(client_obj.id), 'items_json': json.dumps(items), 'action': 'save_send', 'invoice_number': ''})
print('POST /cars/maintenance/add/ status_code:', resp.status_code)
# Check invoices and invoice items created
inv_count = Invoice.objects.filter(client=client_obj).count()
invitem_count = InvoiceItem.objects.count()
part_after = Part.objects.get(id=part.id)
print('Invoice count for client:', inv_count)
print('InvoiceItem total count:', invitem_count)
print('Part quantity after attempt:', part_after.quantity)

if inv_count == 0:
    print('PASS: creation blocked when Part.quantity=0')
else:
    print('FAIL: invoice created despite Part.quantity=0')

# Test B: edit invoice to exceed stock
print('\nTEST B: edit existing invoice to increase qty > stock')
# Setup: create part with quantity 1 and an invoice with qty=1
Part.objects.filter(code__startswith='TEST-B').delete()
partb = Part.objects.create(name='TEST_PART_B', code='TEST-B', quantity=1, track_stock=True, purchase_price=1.0, sale_price=5.0, is_sale=True)
# create invoice and item directly
inv = Invoice.objects.create(invoice_number='INV-TEST-0001', client=client_obj, amount=5.0, paid=False, created_at=timezone.now())
InvoiceItem.objects.create(invoice=inv, description=partb.name, quantity=1, rate=partb.sale_price, discount=0, total=5.0)
# Simulate stock now zero (another sale happened)
partb.quantity = 0
partb.save()

# Now attempt to edit invoice increasing qty to 2 via POST to edit_invoice view
User = get_user_model()
user = User.objects.create_user(username='testman', email='t@t.com', password='pw12345')
client2 = TestClient()
client2.force_login(user)
# prepare items_json with qty 2
items_edit = [{'description': partb.name, 'qty': 2, 'rate': float(partb.sale_price), 'disc': 0}]
resp2 = client2.post(f'/invoices/edit/{inv.id}/', data={'items_json': json.dumps(items_edit), 'amount': '', 'discount': '', 'created_at': ''})
print('POST /invoices/edit/ status_code:', resp2.status_code)
# reload invoice items and part
inv_refreshed = Invoice.objects.get(id=inv.id)
items_after = list(InvoiceItem.objects.filter(invoice=inv_refreshed).values('description','quantity','total'))
partb_after = Part.objects.get(id=partb.id)
print('Invoice items after edit attempt:', items_after)
print('Part quantity after edit attempt:', partb_after.quantity)

if any(float(it['quantity']) > 1 for it in items_after):
    print('FAIL: edit allowed increasing quantity beyond stock')
else:
    print('PASS: edit prevented increasing quantity beyond stock')

print('\nManual tests complete')
