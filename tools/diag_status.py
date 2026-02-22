import os
import sys
import django
from collections import Counter

# ensure project root is on sys.path so Django settings package can be imported
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
django.setup()


from cars.models import Car
try:
    from cars.views import derive_car_status
except Exception as e:
    print('Error importing derive_car_status:', e)
    derive_car_status = None

cars = list(Car.objects.all())
print('Total cars:', len(cars))

db_counts = Counter([c.status for c in cars])
print('\nDB status counts:')
for k,v in db_counts.items():
    print(f'  {k}: {v}')

if derive_car_status:
    derived = [derive_car_status(c) for c in cars]
    derived_counts = Counter(derived)
    print('\nDerived status counts:')
    for k,v in derived_counts.items():
        print(f'  {k}: {v}')

    mismatches = [(c.id, c.plate_number, c.status, derive_car_status(c)) for c in cars if derive_car_status(c) != c.status]
    print('\nMismatches count:', len(mismatches))
    for m in mismatches[:50]:
        print(m)
else:
    print('\nCannot compute derived statuses (derive_car_status missing).')

# Show cars with no maintenance records but status != 'waiting'
no_records = [c for c in cars if not c.maintenance_records.exists() and c.status != 'waiting']
print('\nCars with no maintenance records but DB status not waiting:', len(no_records))
for c in no_records[:30]:
    print(c.id, c.plate_number, c.status)
