from inventory.models import Part
for p in Part.objects.all().order_by('code','name'):
    print(f"{p.code} {p.name}")
