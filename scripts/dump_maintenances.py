# Dump last maintenance records
import os, sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()
from cars.maintenance_models import MaintenanceRecord
for m in MaintenanceRecord.objects.order_by('-id')[:10]:
    print(m.id, getattr(m.service,'id',None), getattr(m.service,'name',None), m.created_at, m.notes)
