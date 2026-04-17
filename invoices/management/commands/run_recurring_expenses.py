from django.core.management.base import BaseCommand
from invoices.models import RecurringExpense, Expense
from django.utils import timezone
import datetime

class Command(BaseCommand):
    help = 'Create Expense records for due RecurringExpense entries'

    def handle(self, *args, **options):
        today = timezone.now().date()
        created = 0

        def advance_date(d, freq, interval=1):
            if freq == 'daily':
                return d + datetime.timedelta(days=interval)
            if freq == 'weekly':
                return d + datetime.timedelta(weeks=interval)
            if freq == 'monthly':
                month = d.month - 1 + interval
                year = d.year + month // 12
                month = month % 12 + 1
                day = min(d.day, 28)
                return datetime.date(year, month, day)
            if freq == 'yearly':
                try:
                    return d.replace(year=d.year + interval)
                except Exception:
                    return d
            return d

        qs = RecurringExpense.objects.filter(active=True, next_date__lte=today)
        for r in qs:
            if r.end_date and r.next_date > r.end_date:
                continue
            # skip flexible items (they are planned but not auto-created)
            if getattr(r, 'is_flexible', False):
                continue
            # skip if auto_create is disabled
            if getattr(r, 'auto_create', True) is False:
                continue
            try:
                # use model helper to centralize creation logic
                r.create_expense()
                created += 1
            except Exception as e:
                self.stderr.write(f"Failed to create expense for {r}: {e}\n")
                continue
            try:
                next_d = advance_date(r.next_date, r.frequency, r.interval)
                r.next_date = next_d
                r.last_run = timezone.now()
                r.save()
            except Exception as e:
                self.stderr.write(f"Failed to advance next_date for {r}: {e}\n")
        self.stdout.write(self.style.SUCCESS(f'Created {created} expense(s).'))
