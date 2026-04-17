import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','workshop.settings')
import django
django.setup()
from invoices.models import Invoice, InvoiceItem
from services.models import Service
from cars.maintenance_models import MaintenanceRecord
from django.db import transaction

created = 0
updated = 0
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()
from invoices.models import Invoice, InvoiceItem
from services.models import Service
from cars.maintenance_models import MaintenanceRecord
from django.db import transaction
from decimal import Decimal

created = 0
updated = 0

changed_invoices = []

with transaction.atomic():
    for inv in Invoice.objects.all():
            # Remove temporary zero-total placeholder items created earlier
            try:
                # remove zero-total placeholder items (use Decimal comparison and case-insensitive match)
                deleted_count, _ = inv.items.filter(total__lte=Decimal('0.0001'), description__iexact='Invoice items (created)').delete()
                if deleted_count:
                    changed_invoices.append((inv.id, deleted_count))
            except Exception:
                pass

            # If invoice already has real items, skip rebuilding
            if inv.items.exists():
                continue

            # Prefer rebuilding items from linked MaintenanceRecord.price when available
            mrs = list(inv.maintenance_records.all())
            if mrs:
                total = 0
                for mr in mrs:
                    rate = float(getattr(mr, 'price', 0) or 0)
                    desc = (mr.service.name if getattr(mr, 'service', None) else (mr.notes or ''))
                    InvoiceItem.objects.create(
                        invoice=inv,
                        service=mr.service,
                        description=desc[:255],
                        quantity=1,
                        rate=rate,
                        discount=0,
                        total=rate
                    )
                    total += rate
                # Recompute and persist using Invoice helper if available
                try:
                    inv.recalc_amount()
                except Exception:
                    inv.amount = total
                    inv.save()
                created += 1
                continue

            # Fallback: create items from invoice.services (legacy behavior)
            svcs = list(inv.services.all())
            if svcs:
                total = 0
                for svc in svcs:
                    rate = getattr(svc, 'default_price', 0) or 0
                    qty = 1
                    discount = 0
                    item_total = qty * float(rate) - float(discount)
                    InvoiceItem.objects.create(
                        invoice=inv,
                        service=svc,
                        description=svc.name,
                        quantity=qty,
                        rate=rate,
                        discount=discount,
                        total=item_total
                    )
                    total += item_total
                try:
                    inv.recalc_amount()
                except Exception:
                    inv.amount = total
                    inv.save()
                created += 1
print('Rebuilt InvoiceItem rows for', created, 'invoices')
if changed_invoices:
    print('Removed placeholder items for invoices:', changed_invoices)
