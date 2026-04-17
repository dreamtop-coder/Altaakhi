"""
LEGACY SCRIPT - DO NOT USE

Replaced by:
scripts/fix_maintenance_prices.py
"""

from cars.maintenance_models import MaintenanceRecord

qs = MaintenanceRecord.objects.filter(invoice__isnull=False, price__lte=0)
print('to-fix count:', qs.count())

for mr in qs:
    try:
        mr.price = float(mr.invoice.amount or 0)
        mr.save()
    except Exception:
        pass

print('done')
