"""
Run this script from the project root to backfill BillLine.account_type when empty/null to 'inventory'.
Usage (from project root):
    python manage.py shell < scripts/backfill_billline_account_type.py

It will print how many rows were updated.
"""
from django.db import transaction
from django.db.models import Q
from bills.models import BillLine

with transaction.atomic():
    qs = BillLine.objects.filter(Q(account_type__isnull=True) | Q(account_type=''))
    count = qs.count()
    if count:
        qs.update(account_type='inventory')
    print(f"Backfilled {count} BillLine rows to 'inventory'.")
