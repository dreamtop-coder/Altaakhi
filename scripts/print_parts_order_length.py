from django.db.models.functions import Length
from inventory.models import Part

parts = Part.objects.annotate(code_length=Length('code')).order_by('code_length','code')
for p in parts:
    print(p.code, p.name)
