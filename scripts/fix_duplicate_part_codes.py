import os
import django
from collections import defaultdict

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
django.setup()

from inventory.models import Part

groups = defaultdict(list)
for p in Part.objects.exclude(code__isnull=True).exclude(code='').order_by('id'):
    key = p.code.strip().lower()
    groups[key].append(p)

total_fixed = 0
for key, parts in groups.items():
    if len(parts) <= 1:
        continue
    # keep the first (lowest id), nullify others
    keeper = parts[0]
    duplicates = parts[1:]
    for p in duplicates:
        print(f'Nullifying code for part id={p.id} name="{p.name}" (was "{p.code}")')
        p.code = None
        p.save()
        total_fixed += 1

print(f'Done. Nullified {total_fixed} duplicate codes.')
