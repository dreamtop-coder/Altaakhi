import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

client = Client()
User = get_user_model()
user = User.objects.first()
if not user:
    print('No user found to login as. Cannot fetch payments page.')
    sys.exit(1)

client.force_login(user)
resp = client.get('/invoices/payments/')
print('Status code:', resp.status_code)
content = resp.content.decode('utf-8', errors='replace')

for ref in ('0000063', '0000064'):
    idx = content.find(ref)
    if idx == -1:
        print(ref, 'not found on page')
    else:
        # print a short surrounding snippet
        start = max(0, idx - 200)
        end = min(len(content), idx + 200)
        snippet = content[start:end].replace('\n', ' ').strip()
        print('\nFound', ref, 'snippet:')
        print(snippet)

print('\nDone.')
