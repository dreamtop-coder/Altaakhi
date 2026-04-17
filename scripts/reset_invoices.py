#!/usr/bin/env python3
"""
Reset invoices in the database.

This script will:
- Back up the project's `db.sqlite3` file to `db.sqlite3.bak.<timestamp>`.
- Delete all `InvoiceItem`, `Payment`, and `Invoice` rows via the Django ORM.
- Attempt to reset the SQLite `sqlite_sequence` entry for invoices_invoice so numbering starts from 1.

Usage:
  python scripts/reset_invoices.py [--yes]

Be careful: this is destructive. Make a manual backup before running if you prefer.
"""
import os
import sys
import shutil
import argparse
import datetime

# ensure project root is on sys.path so `workshop` package can be imported
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
try:
    import django
    django.setup()
except Exception as e:
    print('Failed to setup Django environment:', e)
    sys.exit(1)

from django.db import transaction

try:
    from invoices.models import Invoice, InvoiceItem, Payment
except Exception as e:
    print('Failed to import invoice models:', e)
    sys.exit(1)


def backup_db():
    # assume project root is parent of scripts/
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_path = os.path.join(project_root, 'db.sqlite3')
    if not os.path.exists(db_path):
        print('db.sqlite3 not found at', db_path)
        return None
    ts = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    bak_path = db_path + f'.bak.{ts}'
    shutil.copy2(db_path, bak_path)
    print('Backed up DB to', bak_path)
    return bak_path


def reset_invoices(confirm=False):
    total_inv = Invoice.objects.count()
    total_items = InvoiceItem.objects.count()
    total_payments = Payment.objects.count()
    print(f'Found {total_inv} invoices, {total_items} invoice items, {total_payments} payments.')
    if total_inv == 0 and total_items == 0 and total_payments == 0:
        print('Nothing to do.')
        return
    if not confirm:
        ans = input('Proceed to delete all invoices and related records? Type YES to confirm: ')
        if ans != 'YES':
            print('Aborted by user.')
            return

    bak = backup_db()
    try:
        with transaction.atomic():
            print('Deleting InvoiceItem records...')
            InvoiceItem.objects.all().delete()
            print('Deleting Payment records...')
            Payment.objects.all().delete()
            print('Deleting Invoice records...')
            Invoice.objects.all().delete()
    except Exception as e:
        print('Error while deleting records:', e)
        print('If the DB was backed up, you can restore from', bak)
        return

    # Try to reset sqlite_sequence for SQLite DBs so invoice IDs start from 1 on next insert
    try:
        from django.db import connection
        engine = connection.settings_dict.get('ENGINE', '')
        if 'sqlite' in engine:
            cur = connection.cursor()
            cur.execute("DELETE FROM sqlite_sequence WHERE name='invoices_invoice';")
            connection.commit()
            print('Reset sqlite_sequence for invoices_invoice (SQLite).')
    except Exception as e:
        print('Could not reset sqlite_sequence (non-fatal):', e)

    print('Finished: invoices and related records removed.')
    if bak:
        print('Backup is at:', bak)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Reset invoices in the local Django DB')
    parser.add_argument('--yes', action='store_true', help='Do not prompt for confirmation')
    args = parser.parse_args()
    reset_invoices(confirm=args.yes)
