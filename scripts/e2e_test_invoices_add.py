import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','workshop.settings')
import django
django.setup()
from django.test import Client
from django.conf import settings
from django.utils import timezone
from clients.models import Client as ClientModel
from inventory.models import Part
from services.models import Service
from invoices.models import InvoiceItem, Invoice
import json

c = Client()
# allow test client host
try:
    if 'testserver' not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS += ['testserver']
except Exception:
    pass

# ensure client is authenticated (login_required on add_invoice)
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    test_user = User.objects.filter(is_staff=True).first()
    if not test_user:
        # create a minimal staff user
        test_user = User.objects.create(username='e2e_test_user', is_staff=True)
        test_user.set_password('e2e')
        test_user.save()
    c.force_login(test_user)
    print('Test client force-logged in as', test_user.username)
except Exception as e:
    print('Could not force-login test client:', e)
# ensure test client can access view
# find or create a client
client_obj = ClientModel.objects.first()
if not client_obj:
    client_obj = ClientModel.objects.create(first_name='E2E', phone='000')

# find a part with quantity >=1 and track_stock True and sale_price>0 if possible
part = Part.objects.filter(is_sale=True, track_stock=True).filter(quantity__gte=1, sale_price__gt=0).order_by('-quantity').first()
temp_changed = False
orig_sale_price = None
orig_track = None
if not part:
    # fallback: pick any sale part and temporarily enable tracking and sale_price
    part = Part.objects.filter(is_sale=True).order_by('-quantity').first()
    if part:
        temp_changed = True
        orig_sale_price = part.sale_price
        orig_track = part.track_stock
        try:
            part.sale_price = part.sale_price if part.sale_price and part.sale_price > 0 else 100
            part.track_stock = True
            part.save()
        except Exception:
            temp_changed = False
if not part:
    print('NO_PART_FOUND')
    sys.exit(1)

# record original stock
orig_qty = part.quantity
print('PART chosen:', part.id, part.name, 'orig_qty=', orig_qty)
# record counts before
before_count = InvoiceItem.objects.count()
before_invoice_count = Invoice.objects.count()

# Build items_json with part_id
items = [
    {
        'part_id': part.id,
        'description': part.name,
        'qty': 1,
        'rate': float(part.sale_price or 0),
        'discount': 0,
        'amount': float(part.sale_price or 0)
    }
]

post_data = {
    'selected_client_id': str(client_obj.id),
    'items_json': json.dumps(items),
    'subject': 'E2E Test',
    'action': 'save_send'
}

# local availability check to debug why view may abort
try:
    from inventory.utils import check_items_availability
    shortages = check_items_availability(items, None)
    print('Local availability check shortages:', shortages)
except Exception as e:
    print('Availability check failed:', str(e))

resp = c.post('/invoices/add/', post_data)
print('POST /invoices/add/ status', resp.status_code)
try:
    print('Response content:', resp.content.decode('utf-8')[:400])
except Exception:
    pass

after_count = InvoiceItem.objects.count()
print('InvoiceItem count before=', before_count, 'after=', after_count)
after_invoice_count = Invoice.objects.count()
print('Invoice count before=', before_invoice_count, 'after=', after_invoice_count)
if after_invoice_count > before_invoice_count:
    new_inv = Invoice.objects.order_by('-id').first()
    try:
        its = list(new_inv.items.all())
        print('New Invoice id=', new_inv.id, 'items_count=', len(its))
    except Exception:
        print('New Invoice id=', getattr(new_inv, 'id', None))
if after_count > before_count:
    last_item = InvoiceItem.objects.order_by('-id').first()
    print('New InvoiceItem:', last_item.id, 'part_id=', last_item.part_id, 'item_type=', last_item.item_type, 'qty=', float(last_item.quantity), 'total=', float(last_item.total))
else:
    print('No new InvoiceItem created')

part.refresh_from_db()
print('PART new_qty=', part.quantity)

# restore part attributes if we changed them for the test
if temp_changed and part:
    try:
        part.sale_price = orig_sale_price
        part.track_stock = orig_track
        part.save()
        print('Restored part sale_price and track_stock')
    except Exception:
        print('Failed to restore part attributes')

# Test sending service_id only
svc = Service.objects.first()
if not svc:
    print('NO_SERVICE_FOUND — skipping service test')
else:
    items2 = [ {'service_id': svc.id, 'qty':1, 'rate': float(svc.default_price or 0), 'description': svc.name} ]
    before_count = InvoiceItem.objects.count()
    resp2 = c.post('/invoices/add/', {'selected_client_id': str(client_obj.id), 'items_json': json.dumps(items2), 'subject': 'E2E service test'})
    after_count = InvoiceItem.objects.count()
    print('Service POST status', resp2.status_code, 'items before=', before_count, 'after=', after_count)
    if after_count > before_count:
        print('SERVICE WAS SAVED (unexpected)')
    else:
        print('SERVICE IGNORED (expected)')

print('E2E TEST COMPLETE')
