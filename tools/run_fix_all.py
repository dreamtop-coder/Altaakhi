import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','workshop.settings_test')
import django
# ensure project root is on sys.path so the `workshop` package is importable
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

django.setup()

from scripts.fix_invoice_items import fix
from invoices.models import Invoice

invoices = list(Invoice.objects.order_by('id')[:50])
print('Will run fix on', len(invoices), 'invoices (first 50)')
for inv in invoices:
    print('Running fix for', inv.invoice_number)
    fix(inv.invoice_number)
