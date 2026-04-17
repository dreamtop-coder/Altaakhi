import os, sys, json
from datetime import datetime

# ensure project root is on sys.path so Django project package can be imported
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()

from cars.models import Car
from invoices.models import Invoice
from cars.maintenance_models import MaintenanceRecord

PLATE = '75871'

out = {'plate': PLATE, 'found': False}
try:
    car = Car.objects.select_related('client').filter(plate_number__iexact=PLATE).first()
    if not car:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        sys.exit(0)
    out['found'] = True
    out['car'] = {
        'id': car.id,
        'plate_number': car.plate_number,
        'status': getattr(car, 'status', None),
        'client_id': car.client.id if car.client else None,
        'client_name': f"{car.client.first_name} {car.client.last_name or ''}" if car.client else None,
        'created_at': car.created_at.isoformat() if getattr(car, 'created_at', None) else None,
    }
    # invoices for this car
    invs = Invoice.objects.filter(car=car).order_by('-created_at')
    out['invoices'] = []
    for i in invs:
        out['invoices'].append({
            'id': i.id,
            'invoice_number': i.invoice_number,
            'amount': str(i.amount),
            'paid': bool(i.paid),
            'created_at': i.created_at.isoformat() if getattr(i, 'created_at', None) else None,
        })
    # maintenance records
    recs = MaintenanceRecord.objects.filter(car=car).order_by('-created_at')
    out['maintenance_records'] = []
    for r in recs:
        out['maintenance_records'].append({
            'id': r.id,
            'service': r.service.name if getattr(r, 'service', None) else None,
            'price': str(getattr(r, 'price', None) or ''),
            'created_at': r.created_at.isoformat() if getattr(r, 'created_at', None) else None,
            'delivery_date': r.delivery_date.isoformat() if getattr(r, 'delivery_date', None) else None,
            'is_finished': bool(getattr(r, 'is_finished', False)),
        })
except Exception as e:
    out['error'] = str(e)

print(json.dumps(out, ensure_ascii=False, indent=2))
