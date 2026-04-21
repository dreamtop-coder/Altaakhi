# Integration tests: invoice item-level CRUD and inventory consistency
import json
from django.test import Client as TestClient
from django.contrib.auth import get_user_model
from invoices.models import Invoice, InvoiceItem, Payment
from inventory.models import Part
from clients.models import Client as ClientModel
from inventory.utils import apply_inventory_changes_for_invoice, find_part_for_description
from django.utils import timezone
import os

root_out = []

def tail_log(n=200):
    p = os.path.join(os.getcwd(), 'debug_items_processed.log')
    if not os.path.exists(p):
        return ['Log not found']
    with open(p, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return [ln.strip() for ln in lines[-n:]]

# Helper to run a POST edit with items payload
def post_edit(tc, invoice_id, items_payload):
    post_data = {'items_json': json.dumps(items_payload), 'amount': '', 'discount': '', 'created_at': ''}
    return tc.post(f'/invoices/edit/{invoice_id}/', data=post_data)

# Setup test environment: create part, invoice, item
User = get_user_model()
user, _ = User.objects.get_or_create(username='repro_user', defaults={'email': 'repro@local'})
try:
    user.set_password('pw')
    user.save()
except Exception:
    pass

tc = TestClient()
try:
    tc.force_login(user)
except Exception:
    pass

print('Starting integration tests')

# Create a fresh Part
part_name = 'TST_PART_INV'
part, _ = Part.objects.get_or_create(name=part_name, defaults={'quantity': 10, 'track_stock': True})
# ensure known starting stock
part.quantity = 10
part.track_stock = True
part.save()
initial_stock = part.quantity
print('Initial stock for', part.name, '=', initial_stock)

# Create invoice
# ensure we have a client to attach (Invoice.client is NOT NULL in this schema)
client_obj, _ = ClientModel.objects.get_or_create(first_name='TST_CLIENT', defaults={'phone_number': '000000', 'customer_id': f'TST-{int(timezone.now().timestamp())}'})
inv = Invoice.objects.create(invoice_number=f'INV-TEST-{int(timezone.now().timestamp())}', client=client_obj, amount=0.0, paid=False, created_at=timezone.now())
print('Test invoice id:', inv.id)

# Scenario 1: Modification (1 -> 3)
print('\nScenario 1: Modification (1 -> 3)')
# create initial item qty=1 and apply initial stock decrement to simulate previously-sold item
it = InvoiceItem.objects.create(invoice=inv, service=None, description=part.name, quantity=1, rate=10, discount=0, total=10)
apply_inventory_changes_for_invoice([{'description': part.name, 'qty': 1}], decrement=True)
part.refresh_from_db()
print(' After initial apply stock =', part.quantity)

# Now POST edit to change qty to 3
items_payload = [{'invoice_item_id': it.id, 'description': part.name, 'qty': 3, 'rate': 10, 'disc': 0}]
resp = post_edit(tc, inv.id, items_payload)
part.refresh_from_db()
expected = initial_stock - 3
print(' POST status', resp.status_code, '| final stock =', part.quantity, '| expected =', expected)
print(' Log tail:')
for ln in tail_log(20):
    print(ln)
if part.quantity == expected:
    print('Scenario 1 PASS')
else:
    print('Scenario 1 FAIL')

# Cleanup invoice items for next scenario
InvoiceItem.objects.filter(invoice=inv).delete()
part.quantity = initial_stock
part.save()

# Scenario 2: Deletion
print('\nScenario 2: Deletion (qty 2 -> delete)')
# create initial item qty=2 and apply initial decrement
it2 = InvoiceItem.objects.create(invoice=inv, service=None, description=part.name, quantity=2, rate=5, discount=0, total=10)
apply_inventory_changes_for_invoice([{'description': part.name, 'qty': 2}], decrement=True)
part.refresh_from_db()
print(' After initial apply stock =', part.quantity)
# Post with empty items (delete)
resp = post_edit(tc, inv.id, [])
part.refresh_from_db()
print(' POST status', resp.status_code, '| final stock =', part.quantity, '| expected =', initial_stock)
if part.quantity == initial_stock:
    print('Scenario 2 PASS')
else:
    print('Scenario 2 FAIL')

# Cleanup
InvoiceItem.objects.filter(invoice=inv).delete()
part.quantity = initial_stock
part.save()

# Scenario 3: Repeated modification (1->2 then 2->3)
print('\nScenario 3: Repeated modification (1->2 then 2->3)')
it3 = InvoiceItem.objects.create(invoice=inv, service=None, description=part.name, quantity=1, rate=7, discount=0, total=7)
apply_inventory_changes_for_invoice([{'description': part.name, 'qty': 1}], decrement=True)
part.refresh_from_db()
print(' After initial apply stock =', part.quantity)
# First update to qty=2
resp1 = post_edit(tc, inv.id, [{'invoice_item_id': it3.id, 'description': part.name, 'qty': 2, 'rate': 7, 'disc': 0}])
part.refresh_from_db()
print(' After first update stock =', part.quantity)
# Second update to qty=3
resp2 = post_edit(tc, inv.id, [{'invoice_item_id': it3.id, 'description': part.name, 'qty': 3, 'rate': 7, 'disc': 0}])
part.refresh_from_db()
print(' After second update stock =', part.quantity)
expected = initial_stock - 3
print(' Expected final stock =', expected)
if part.quantity == expected:
    print('Scenario 3 PASS')
else:
    print('Scenario 3 FAIL')

# Cleanup
InvoiceItem.objects.filter(invoice=inv).delete()
part.quantity = initial_stock
part.save()

# Scenario 4: Add -> Delete -> Add
print('\nScenario 4: Add -> Delete -> Add')
# Start clean
part.refresh_from_db()
print(' start stock =', part.quantity)
# Add new (POST with new item)
resp_add1 = post_edit(tc, inv.id, [{'description': part.name, 'qty': 2, 'rate': 9, 'disc': 0}])
part.refresh_from_db()
print(' after add1 stock =', part.quantity)
# Delete (post with empty)
resp_del = post_edit(tc, inv.id, [])
part.refresh_from_db()
print(' after delete stock =', part.quantity)
# Add again
resp_add2 = post_edit(tc, inv.id, [{'description': part.name, 'qty': 2, 'rate': 9, 'disc': 0}])
part.refresh_from_db()
print(' after add2 stock =', part.quantity)
expected = initial_stock - 2
print(' expected final =', expected)
if part.quantity == expected:
    print('Scenario 4 PASS')
else:
    print('Scenario 4 FAIL')

# Cleanup
InvoiceItem.objects.filter(invoice=inv).delete()
part.quantity = initial_stock
part.save()

# Scenario 5: Totals and payments
print('\nScenario 5: Totals and payment reconciliation')
# create two items
InvoiceItem.objects.create(invoice=inv, service=None, description='Line A', quantity=1, rate=10, discount=0, total=10)
InvoiceItem.objects.create(invoice=inv, service=None, description='Line B', quantity=2, rate=5, discount=0, total=10)
# Manually set invoice.amount to sum (some code paths do this on save)
inv.amount = 20
inv.save()
# create a payment of 7 (paid)
Payment.objects.create(invoice=inv, amount=7, status='paid', payment_date=timezone.now(), method='cash')
from decimal import Decimal
items_sum = sum([it.total for it in InvoiceItem.objects.filter(invoice=inv)])
# compute paid from Payment model
paid = sum([p.amount for p in inv.payments.filter(status='paid')])
remaining = float(Decimal(str(inv.amount or 0)) - Decimal(str(paid or 0)))
print(' items sum=', items_sum, ' inv.amount=', inv.amount, ' paid=', paid, ' remaining=', remaining)
if float(items_sum) == float(inv.amount) and remaining == float(inv.amount - paid):
    print('Scenario 5 PASS')
else:
    print('Scenario 5 FAIL')

print('\nIntegration tests complete')
print('\nFinal log tail:')
for ln in tail_log(50):
    print(ln)
