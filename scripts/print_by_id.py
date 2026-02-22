from inventory.models import Part
print('--- order by id ---')
for p in Part.objects.all().order_by('id'):
    print(p.id, p.code, p.name)
