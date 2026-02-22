import os, sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()

from django.test import Client
from cars.models import Car
from cars.maintenance_models import MaintenanceRecord
from services.models import Service
from django.utils import timezone
from cars.views import derive_car_status

plate = '70016'
car = Car.objects.filter(plate_number=plate).first()
if not car:
    print('Car not found', plate); sys.exit(1)

print('Before create: car.status=', car.status, 'derived=', derive_car_status(car))

svc = Service.objects.first()
if not svc:
    from services.models import Service as S
    svc = S.objects.create(name='Repro Service', default_price=50)

mr = MaintenanceRecord.objects.create(car=car, service=svc, price=60, notes='Ajax repro', created_at=timezone.now(), is_finished=False)
print('Created MR', mr.id)
car.refresh_from_db()
print('After create: car.status=', car.status, 'derived=', derive_car_status(car))

c = Client()
resp = c.get('/cars/ajax/filter/?status=in_progress')
print('AJAX status:', resp.status_code)
text = resp.content.decode('utf-8')
found = plate in text
print('Plate present in AJAX response:', found)
# For debugging, print a snippet around first occurrence
if found:
    idx = text.find(plate)
    print('...snippet:', text[max(0, idx-80):idx+80])
else:
    # save HTML to file for inspection
    with open('tools/repro_ajax_response.html','w',encoding='utf-8') as f:
        f.write(text)
    print('Saved AJAX response to tools/repro_ajax_response.html')

print('Done')
