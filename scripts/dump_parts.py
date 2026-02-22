from inventory.models import Part
parts = Part.objects.all().order_by('id')
print('Total parts:', parts.count())
for p in parts:
    print(p.id, repr(p.code), p.name)
