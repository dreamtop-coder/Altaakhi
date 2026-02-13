# Simulate the mapping logic from views_add_maintenance.py
import os, sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()
import json
from services.models import Service
from inventory.models import Part as InvPart

p = InvPart.objects.order_by('-id').first()
parts_list = [{'id': p.pk, 'name': p.name, 'qty': 1, 'unit': float(p.sale_price or 0), 'is_service': True}]
print('parts_list:', parts_list)
service = None
# mapping logic
from inventory.models import Part as InvPart
for it in parts_list:
    name_to_match = None
    if it.get('is_service') or it.get('service_id'):
        if it.get('id'):
            try:
                pid = int(it.get('id') or 0)
                p2 = InvPart.objects.filter(pk=pid).first()
                if p2:
                    name_to_match = getattr(p2, 'name', None)
            except Exception:
                name_to_match = it.get('name')
        else:
            name_to_match = it.get('name')
        if name_to_match:
            svc = Service.objects.filter(name__iexact=(name_to_match or '').strip()).first()
            print('lookup name_to_match ->', repr(name_to_match), 'svc=', getattr(svc,'id',None))
            if svc:
                service = svc
                break

print('result service:', getattr(service,'id',None), getattr(service,'name',None))
