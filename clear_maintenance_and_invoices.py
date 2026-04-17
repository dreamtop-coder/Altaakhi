import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()
from cars.models import MaintenanceRecord
from invoices.models import Invoice
import sys

# Safety: require explicit confirmation to perform destructive clear.
# Run with `--confirm` or set environment var `CONFIRM_CLEAR=1` to allow deletion.
confirm = ('--confirm' in sys.argv) or (os.environ.get('CONFIRM_CLEAR') == '1')

print('This script will DELETE ALL MaintenanceRecord and Invoice rows.')
print('Run with --confirm or set CONFIRM_CLEAR=1 to proceed.')
print('Summary (counts):')
print('  MaintenanceRecord:', MaintenanceRecord.objects.count())
print('  Invoice:', Invoice.objects.count())

if confirm:
	MaintenanceRecord.objects.all().delete()
	Invoice.objects.all().delete()
	print('All maintenance records and invoices deleted successfully.')
else:
	print('No destructive action taken. Pass --confirm to actually delete.')
