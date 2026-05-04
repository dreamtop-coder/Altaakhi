import json
from django.test import Client
c = Client()
payload = {
    'selected_client_id': '10',
    'plate_number': '70016',
    'selected_client_car': '10',
    'invoice_number': 'INV-000001',
    'maintenance_date': '2026-05-02',
    'items_json': json.dumps([
        {'part_id': '3', 'description': 'Brake Adjustments', 'qty': 1, 'rate': 20, 'discount': 0, 'amount': 20}
    ]),
    'action': 'save_send'
}
r = c.post('/maintenance/add/', payload)
print('STATUS', r.status_code)
print('CONTENT', r.content.decode('utf-8')[:2000])
print('\n--- END ---')
