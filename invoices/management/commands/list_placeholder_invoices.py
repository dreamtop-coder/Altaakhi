from django.core.management.base import BaseCommand
from django.db.models import Count

class Command(BaseCommand):
    help = 'List placeholder invoices (amount==0, no items, no payments). Use --delete --yes to remove.'

    def add_arguments(self, parser):
        parser.add_argument('--delete', action='store_true', help='Delete found placeholder invoices')
        parser.add_argument('--yes', action='store_true', help='Confirm deletion (use with --delete)')

    def handle(self, *args, **options):
        from invoices.models import Invoice

        qs = Invoice.objects.annotate(items_count=Count('items'), payments_count=Count('payments')).filter(
            amount__lte=0, items_count=0, payments_count=0
        ).order_by('id')

        if not qs.exists():
            self.stdout.write('No placeholder invoices found.')
            return

        self.stdout.write('Placeholder invoices: (id, invoice_number, amount, client_id, car_plate, created_at)')
        ids = []
        for inv in qs:
            car_plate = getattr(inv.car, 'plate_number', None)
            self.stdout.write(f'{inv.id} {inv.invoice_number} {float(inv.amount)} {inv.client_id} {car_plate} {inv.created_at}')
            ids.append(inv.id)

        if options.get('delete'):
            if not options.get('yes'):
                self.stdout.write('\nTo delete these invoices run with: --delete --yes')
                return
            Invoice.objects.filter(id__in=ids).delete()
            self.stdout.write(f'Deleted {len(ids)} invoices')
        else:
            self.stdout.write('\nRun with --delete --yes to remove these (make a DB backup first).')
