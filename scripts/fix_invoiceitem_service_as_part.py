import os
import sys
from pathlib import Path
import shutil
import json
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()
from invoices.models import InvoiceItem
from decimal import Decimal

# Make DB backup
DB = ROOT / 'db.sqlite3'
if not DB.exists():
    print('No db.sqlite3 found; aborting')
    sys.exit(1)

ts = datetime.now().strftime('%Y%m%dT%H%M%S')
backup_path = ROOT / f'db.sqlite3.pre_fix.{ts}'
shutil.copy2(DB, backup_path)
print('DB backup created:', str(backup_path))

# Prepare undo log
undo_log = {
    'timestamp': ts,
    'script': 'fix_invoiceitem_service_as_part.py',
    'changes': []
}

items = InvoiceItem.objects.filter(item_type='part', service_id__isnull=False)
print('Fixing items:', items.count())
fixed = 0
errors = 0
for item in items:
    orig = {
        'id': item.id,
        'item_type': item.item_type,
        'rate': str(item.rate) if item.rate is not None else None,
        'total': str(item.total) if item.total is not None else None,
        'quantity': str(item.quantity) if item.quantity is not None else None,
        'discount': str(item.discount) if item.discount is not None else None,
        'service_id': item.service_id,
        'part_id': item.part_id,
        'description': item.description,
    }
    try:
        # record original
        undo_log['changes'].append(orig)

        # apply fix
        item.item_type = 'service'
        # if rate is zero or null, set from service.default_price
        try:
            r = Decimal(str(item.rate))
        except Exception:
            r = Decimal('0')
        if (r == Decimal('0') or r is None) and item.service:
            try:
                item.rate = item.service.default_price or item.rate
            except Exception:
                pass
        # save will recompute total
        item.save()
        fixed += 1
    except Exception as e:
        print(f'Error on item {item.id}:', e)
        errors += 1

# write undo log
log_path = ROOT / f'scripts/fix_invoiceitem_service_as_part.undo.{ts}.json'
with open(log_path, 'w', encoding='utf-8') as f:
    json.dump(undo_log, f, ensure_ascii=False, indent=2)

print('Fixed:', fixed)
print('Errors:', errors)
remaining = InvoiceItem.objects.filter(item_type='part', service_id__isnull=False).count()
print('Remaining wrong:', remaining)
print('Undo log:', str(log_path))
print('If anything is wrong, restore DB from the backup file above.')
