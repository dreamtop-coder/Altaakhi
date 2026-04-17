import os, json, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE','workshop.settings_test')
project_root = r'C:\Users\Mahdi\Desktop\Altaakhi Workshop'
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import django
django.setup()
from django.test import Client
from inventory.models import Part
p = Part.objects.filter(name__iexact='Turbo').first()
print('Turbo qty before', getattr(p,'quantity',None))
client = Client()
from django.contrib.auth import get_user_model
User = get_user_model()
user, _ = User.objects.get_or_create(username='test_bill')
user.set_password('test')
user.save()
client.force_login(user)
from inventory.models import Supplier
sup = Supplier.objects.first()
sup_id = sup.id if sup else ''
items = [{'description': 'Turbo', 'qty': 10, 'rate': 10, 'discount': 0}]
post = {'items_json': json.dumps(items), 'bill_number': 'BIL-TEST', 'selected_supplier_id': sup_id, 'account': 'A1', 'action': 'save'}
resp = client.post('/bills/add/', post, follow=True, HTTP_HOST='127.0.0.1')
print('Status', resp.status_code)
print('Contains Arabic?', 'الكمية غير متوفرة' in resp.content.decode(errors='ignore'))
