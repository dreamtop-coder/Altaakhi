from django.core.management.base import BaseCommand

from cars.maintenance_models import MaintenanceRecord


class Command(BaseCommand):
    help = "Fix MaintenanceRecord.price from linked Invoice"

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', dest='dry_run', help='Show records that would be changed without saving.')

    def handle(self, *args, **options):
        dry = options.get('dry_run', False)
        qs = MaintenanceRecord.objects.filter(invoice__isnull=False, price__lte=0)
        count = qs.count()
        self.stdout.write(f"Found {count} maintenance record(s) with missing/zero price.")

        updated = 0
        for mr in qs.select_related('invoice'):
            new_price = float(mr.invoice.amount or 0)
            self.stdout.write(f"MR id={mr.id} invoice_id={getattr(mr.invoice,'id',None)} current_price={mr.price} -> new_price={new_price}")
            if not dry:
                mr.price = new_price
                mr.save()
                updated += 1

        if dry:
            self.stdout.write(self.style.WARNING("Dry run complete — no changes saved."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Updated {updated} record(s)."))
