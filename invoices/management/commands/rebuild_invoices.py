from decimal import Decimal
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Safely rebuild invoice items and recalculate invoice amounts"

    def handle(self, *args, **kwargs):
        from invoices.models import Invoice, InvoiceItem
        from cars.maintenance_models import MaintenanceRecord

        processed = 0
        rebuilt = 0
        removed_placeholders = []

        for inv in Invoice.objects.all():
            # remove zero-total placeholder items with exact placeholder description
            try:
                deleted_count, _ = inv.items.filter(total__lte=Decimal('0.0001'), description__iexact='Invoice items (created)').delete()
            except Exception:
                deleted_count = 0
            if deleted_count:
                removed_placeholders.append((inv.id, deleted_count))

            # if there are already real items, skip rebuilding
            if inv.items.exists():
                # ensure amount is consistent
                try:
                    inv.recalc_amount()
                except Exception:
                    pass
                processed += 1
                continue

            # rebuild from maintenance records when available
            mrs = list(inv.maintenance_records.all())
            if mrs:
                total = Decimal('0')
                for mr in mrs:
                    try:
                        rate = Decimal(str(getattr(mr, 'price', 0) or 0))
                    except Exception:
                        rate = Decimal('0')
                    desc = (mr.service.name if getattr(mr, 'service', None) else (mr.notes or ''))
                    InvoiceItem.objects.create(
                        invoice=inv,
                        service=mr.service,
                        description=(desc or '')[:255],
                        quantity=Decimal('1'),
                        rate=rate,
                        discount=Decimal('0'),
                        total=rate
                    )
                    total += rate
                try:
                    inv.recalc_amount()
                except Exception:
                    inv.amount = total
                    inv.save()
                rebuilt += 1
            else:
                # fallback: if invoice.services exist, create items from service.default_price
                svcs = list(inv.services.all())
                if svcs:
                    total = Decimal('0')
                    for svc in svcs:
                        try:
                            rate = Decimal(str(getattr(svc, 'default_price', 0) or 0))
                        except Exception:
                            rate = Decimal('0')
                        InvoiceItem.objects.create(
                            invoice=inv,
                            service=svc,
                            description=(svc.name or '')[:255],
                            quantity=Decimal('1'),
                            rate=rate,
                            discount=Decimal('0'),
                            total=rate
                        )
                        total += rate
                    try:
                        inv.recalc_amount()
                    except Exception:
                        inv.amount = total
                        inv.save()
                    rebuilt += 1

            processed += 1

        self.stdout.write(self.style.SUCCESS(f"Processed {processed} invoices, rebuilt items for {rebuilt} invoices"))
        if removed_placeholders:
            self.stdout.write(self.style.WARNING(f"Removed placeholder items for invoices: {removed_placeholders}"))
