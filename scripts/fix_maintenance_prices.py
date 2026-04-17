"""
Fix MaintenanceRecord prices from linked Invoice.

Usage (Windows PowerShell):
Get-Content scripts/fix_maintenance_prices.py | python manage.py shell

Use this script if MaintenanceRecord.price is missing or incorrect.
"""

from cars.maintenance_models import MaintenanceRecord

qs = MaintenanceRecord.objects.filter(invoice__isnull=False, price__lte=0)
print('to-fix count:', qs.count())
for mr in qs:
    try:
        mr.price = float(mr.invoice.amount or 0)
        mr.save()
    except Exception as e:
        print('failed to update MR id=%s: %s' % (getattr(mr, 'id', '(unknown)'), str(e)))
print('done')
