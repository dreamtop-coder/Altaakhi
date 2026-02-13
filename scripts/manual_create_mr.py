# manual create maintenance record test
import os, sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()
from cars.models import Car
from services.models import Service
from cars.maintenance_models import MaintenanceRecord
from decimal import Decimal
from datetime import datetime
car = Car.objects.order_by('-id').first()
service = Service.objects.filter(name__iexact='Test Service X').first()
m = MaintenanceRecord.objects.create(car=car, service=service, price=Decimal('0.00'), notes='manual test', created_at=datetime.utcnow())
print('manual create id', m.id, 'service_id', getattr(m.service,'id',None))
