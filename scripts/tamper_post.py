import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()

from django.test import Client
from django.conf import settings

# Force enforcement for this run
try:
    setattr(settings, 'CONTEXT_GUARD_ENFORCE', True)
except Exception:
    pass

c = Client()
# tampered client id that should be overridden by ContextGuard when locked
data = {
    'selected_client_id': '99999',
    'selected_client_car': '',
    'plate_number': '',
    'maintenance_date': '2026-05-11',
    'items_json': '[{"description": "TamperTest", "qty": 1, "rate": 5, "discount": 0}]',
}
print('Posting tampered data to /maintenance/add/?car_id=20')
resp = c.post('/maintenance/add/?car_id=20', data)
print('Response status:', resp.status_code)
# dump last lines of debug logs to help verification
for fname in ('debug_context_guard.log','debug_post_dump.log'):
    try:
        print('\n---', fname, 'last 40 lines ---')
        with open(fname, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()[-40:]
            for l in lines:
                print(l.rstrip('\n'))
    except Exception as e:
        print('Error reading', fname, e)
