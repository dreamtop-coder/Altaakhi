# Debug script: inspect last inventory part and matching Service
import os, sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()
from services.models import Service
from inventory.models import Part as InvPart
p = InvPart.objects.order_by('-id').first()
print('InvPart latest id,name:', p.pk, repr(p.name))
print('Service exact matches:', list(Service.objects.filter(name__iexact=p.name).values_list('id','name')))
print('Imported services:', list(Service.objects.filter(department__name='Imported').values_list('id','name')))
