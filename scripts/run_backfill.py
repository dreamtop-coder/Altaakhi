"""
Standalone backfill runner: sets up Django and backfills BillLine.account_type to 'inventory'.
Run from project root: python scripts/run_backfill.py
"""
import os
import sys

# Ensure project root is on path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')

import django
django.setup()

from django.db import transaction
from django.db.models import Q
from bills.models import BillLine

with transaction.atomic():
    qs = BillLine.objects.filter(Q(account_type__isnull=True) | Q(account_type=''))
    count = qs.count()
    if count:
        qs.update(account_type='inventory')
    print(f"Backfilled {count} BillLine rows to 'inventory'.")
