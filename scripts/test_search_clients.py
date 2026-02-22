import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','workshop.settings')
import django
django.setup()
from django.test import RequestFactory
from clients.views import search_clients_api
from django.http import JsonResponse

rf = RequestFactory()
for q in ['', 'ma']:
    req = rf.get('/clients/search/', {'q': q})
    resp = search_clients_api(req)
    print('q=', repr(q), 'status=', resp.status_code)
    try:
        print(resp.content.decode('utf-8'))
    except Exception as e:
        print('decode error', e)
