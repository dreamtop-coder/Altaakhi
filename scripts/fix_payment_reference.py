import os
import sys
import json
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()

from django.apps import apps

Payment = apps.get_model('invoices', 'Payment')
Client = apps.get_model('clients', 'Client')

TARGET_REF = '0000063'
NEW_REF = '0000064'
TARGET_CLIENT_FULL = 'عبدالله حسين حمد مبارك'

qs = Payment.objects.filter(reference=TARGET_REF).select_related('client', 'invoice')
payments = []
for p in qs:
    client_name = str(p.client) if p.client else None
    payments.append({
        'id': p.id,
        'reference': p.reference,
        'amount': str(p.amount),
        'payment_date': p.payment_date.isoformat() if p.payment_date else None,
        'method': p.method,
        'status': p.status,
        'client_id': p.client_id,
        'client_name': client_name,
        'invoice_id': p.invoice_id,
    })

backup_path = os.path.join(os.path.dirname(__file__), f'payments_{TARGET_REF}_backup.json')
with open(backup_path, 'w', encoding='utf-8') as f:
    json.dump(payments, f, ensure_ascii=False, indent=2)

print(f'Wrote backup of {len(payments)} payment(s) to {backup_path}')
if not payments:
    sys.exit(0)

# Find payment for target client
target = None
for p in qs:
    name = str(p.client) if p.client else ''
    if name.strip() == TARGET_CLIENT_FULL:
        target = p
        break

if not target:
    # try contains
    for p in qs:
        name = str(p.client) if p.client else ''
        if 'عبدالله' in name:
            target = p
            break

if not target:
    print('No payment found matching client', TARGET_CLIENT_FULL)
    print('Payments found:')
    for p in payments:
        print(' -', p['id'], p['client_name'], p['amount'])
    sys.exit(1)

old_ref = target.reference
print('Updating payment id', target.id, 'client=', str(target.client), 'from', old_ref, 'to', NEW_REF)
target.reference = NEW_REF
target.save()
print('Updated.')
