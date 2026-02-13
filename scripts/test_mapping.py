import os, sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()
from inventory.models import Part as InvPart
from services.models import Service

p = InvPart.objects.filter(name__icontains='Test Service X').first()
if not p:
    print('Part not found')
else:
    print('Part id', p.pk, 'name', p.name)
    svc = Service.objects.filter(name__iexact=p.name).first()
    if svc:
        print('Mapped Service id', svc.pk, 'name', svc.name)
    else:
        print('No matching Service by name')
