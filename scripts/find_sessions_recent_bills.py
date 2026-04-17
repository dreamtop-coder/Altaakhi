import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import django
django.setup()
from django.contrib.sessions.models import Session

print('Scanning sessions for "recent_bills"...')
count=0
for s in Session.objects.all():
    try:
        data = s.get_decoded()
    except Exception:
        continue
    if data and 'recent_bills' in data and data['recent_bills']:
        count+=1
        print('---')
        print('session_key:', s.session_key)
        print('modified:', s.expire_date)
        rb = data['recent_bills']
        print('recent_bills count:', len(rb))
        for i, b in enumerate(rb[:5]):
            print(' idx', i, 'number:', b.get('number') or b.get('bill_number'), 'amount:', b.get('amount') or b.get('grand_total'))
print('Found', count, 'sessions with recent_bills')
