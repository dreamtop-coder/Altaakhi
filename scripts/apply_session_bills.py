#!/usr/bin/env python
"""Apply session-stored bills (key: 'recent_bills') to Supplier.amount.

This script is idempotent: it marks processed sessions with '_recent_bills_applied'
so running it again won't double-apply the same session data.

Run from project root with the project's Python (virtualenv):
  .venv\Scripts\python.exe scripts\apply_session_bills.py
"""
import os
import sys
from decimal import Decimal, InvalidOperation

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
# ensure project root is on sys.path so Django can import the project package
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import django
django.setup()

import argparse
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from inventory.models import Supplier
from django.db import transaction


def apply_session_bills(dry_run=False):
    sessions = Session.objects.all()
    updated = {}
    sessions_processed = 0
    for s in sessions:
        try:
            store = SessionStore(session_key=s.session_key)
            data = store.load()
        except Exception:
            continue
        if not data:
            continue
        if data.get('_recent_bills_applied'):
            continue
        recent = data.get('recent_bills')
        if not recent:
            continue
        sessions_processed += 1
        for bill in recent:
            vendor = bill.get('vendor_name') or ''
            amount_raw = bill.get('amount')
            if not vendor or not amount_raw:
                continue
            try:
                amt = Decimal(str(amount_raw))
            except (InvalidOperation, TypeError):
                continue
            if amt == Decimal('0'):
                continue
            # try to find supplier by exact or case-insensitive name
            sup = Supplier.objects.filter(name__iexact=vendor).first()
            if not sup:
                # try contains fallback
                sup = Supplier.objects.filter(name__icontains=vendor).first()
            if not sup:
                continue
            try:
                # perform update inside transaction and with row lock
                if not dry_run:
                    with transaction.atomic():
                        locked = Supplier.objects.select_for_update().filter(pk=sup.pk).first()
                        locked.amount = (locked.amount or Decimal('0')) + amt
                        locked.save()
                # record planned update
                updated.setdefault(sup.id, {'name': sup.name, 'added': Decimal('0')})
                updated[sup.id]['added'] += amt
            except Exception:
                continue
        # mark session as applied and save
        try:
            if not dry_run:
                data['_recent_bills_applied'] = True
                for k, v in data.items():
                    store[k] = v
                store.save()
            else:
                # report that we'd mark the session as applied
                pass
        except Exception:
            pass

    # report
    print(f"Sessions processed: {sessions_processed}")
    if not updated:
        print("No supplier balances updated.")
    else:
        print("Updated suppliers:")
        for sid, info in updated.items():
            print(f" - ID={sid} Name={info['name']} Added={info['added']}")


def parse_args():
    p = argparse.ArgumentParser(description='Apply session-stored bills to Supplier.amount')
    p.add_argument('--dry-run', action='store_true', help='Show planned supplier updates without saving.')
    return p.parse_args()


if __name__ == '__main__':
    args = parse_args()
    apply_session_bills(dry_run=args.dry_run)
