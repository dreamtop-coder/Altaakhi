from inventory.models import Part
from django.db.models import Value

print('ORDER BY code,name:')
for p in Part.objects.all().order_by('code','name'):
    print(p.id, repr(p.code), len(p.code) if p.code else None, p.name)

print('\nORDER BY name:')
for p in Part.objects.all().order_by('name'):
    print(p.id, repr(p.code), len(p.code) if p.code else None, p.name)

print('\nORDER BY id:')
for p in Part.objects.all().order_by('id'):
    print(p.id, repr(p.code), len(p.code) if p.code else None, p.name)
