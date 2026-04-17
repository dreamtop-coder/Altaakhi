from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from bills.services import migrate_session_bill


class Command(BaseCommand):
    help = 'Migrate session-stored bills (request.session["recent_bills"]) into persistent Bill/BillLine records.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Run migration in dry-run mode (no DB writes).')

    def handle(self, *args, **options):
        dry = options.get('dry_run', False)
        sessions = Session.objects.all()
        total = 0
        migrated = 0
        migrated_dry = 0
        skipped = 0
        for s in sessions:
            data = s.get_decoded()
            recent = data.get('recent_bills') or []
            if not recent:
                continue
            for sb in recent:
                total += 1
                # attempt migration (pass dry flag through)
                bill, reason = migrate_session_bill(sb, dry_run=dry)
                if bill:
                    if dry:
                        migrated_dry += 1
                        self.stdout.write(f'Dry-run: would migrate bill {sb.get("number") or sb.get("bill_number")}')
                    else:
                        migrated += 1
                        try:
                            self.stdout.write(self.style.SUCCESS(f'Migrated bill {bill.bill_number} (id={bill.id})'))
                        except Exception:
                            self.stdout.write(self.style.SUCCESS('Migrated bill (id unknown)'))
                else:
                    skipped += 1
                    self.stdout.write(self.style.WARNING(f'Skipped bill ({sb.get("number")}) reason={reason}'))
        if dry:
            self.stdout.write(self.style.SUCCESS(f'Total found: {total}, dry-run planned: {migrated_dry}, skipped: {skipped}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Total found: {total}, migrated: {migrated}, skipped: {skipped}'))
