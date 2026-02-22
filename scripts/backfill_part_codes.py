from django.db import transaction
from django.db.models import Q
from inventory.models import Part

parts = Part.objects.filter(Q(code__isnull=True) | Q(code__exact='')).order_by('id')
if not parts.exists():
    print('No parts need backfill.')
else:
    print(f'Backfilling {parts.count()} parts...')
    for p in parts:
        try:
            # ensure code is empty so save() will auto-generate
            p.code = None
            p.save()
            print(f'Assigned code {p.code} to part id={p.id} name="{p.name}"')
        except Exception as e:
            print('Failed for part', p.id, str(e))
print('Done.')
