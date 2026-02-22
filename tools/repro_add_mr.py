import os, sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()

from cars.models import Car
from cars.maintenance_models import MaintenanceRecord
from services.models import Service
from django.utils import timezone

plate = '70016'
car = Car.objects.filter(plate_number=plate).first()
if not car:
    print('Car not found', plate); sys.exit(1)

from cars.views import derive_car_status
print('Before: car.status=', car.status, 'derived=', derive_car_status(car))

# Choose a service
svc = Service.objects.first()
if not svc:
    from services.models import Service as S
    svc = S.objects.create(name='Repro Service', default_price=50)

# Create a new maintenance record (not finished, no delivery)
mr = MaintenanceRecord.objects.create(
    car=car,
    service=svc,
    price=50,
    notes='Repro test',
    created_at=timezone.now(),
    is_finished=False
)
print('Created MR', mr.id)
# Refresh car from DB
car.refresh_from_db()
print('After create: car.status=', car.status, 'derived=', derive_car_status(car))

# Print latest maintenance records
for r in car.maintenance_records.order_by('created_at'):
    print('MR', r.id, 'is_finished=', r.is_finished, 'delivery_date=', r.delivery_date, 'created_at=', r.created_at)

print('Done')
