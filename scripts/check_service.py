import json
from services.models import Service
from cars.maintenance_models import MaintenanceRecord

try:
    s = Service.objects.get(pk=1)
except Service.DoesNotExist:
    print(json.dumps({'error': 'Service with id=1 not found'}))
else:
    data = {
        'id': s.id,
        'name': str(s),
        'car': str(s.car) if s.car else None,
        'invoices_count': s.invoices.count(),
        'invoices_ids': list(s.invoices.values_list('id', flat=True)[:50]),
        'invoice_items_count': s.invoice_items.count(),
        'invoice_items_ids': list(s.invoice_items.values_list('id', flat=True)[:50]),
        'payments_count': s.payments.count(),
        'payments_ids': list(s.payments.values_list('id', flat=True)[:50]),
    }
    maint_qs = MaintenanceRecord.objects.filter(service=s)
    data['maintenance_count'] = maint_qs.count()
    data['maintenance_ids'] = list(maint_qs.values_list('id', flat=True)[:50])
    print(json.dumps(data, ensure_ascii=False, default=str))
