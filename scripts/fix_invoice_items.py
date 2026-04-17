#!/usr/bin/env python
"""Fix invoice by adding missing InvoiceItem rows from linked MaintenanceRecord entries.

Usage: python scripts/fix_invoice_items.py INV-000062
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
# ensure project root is on sys.path so `workshop` package is importable when running the script
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
django.setup()

from invoices.models import Invoice, InvoiceItem
from cars.maintenance_models import MaintenanceRecord
from django.db.models import Sum
from decimal import Decimal
from django.db import transaction

# Try to import inventory helpers (may not exist in minimal environments)
try:
    from inventory.utils import check_items_availability, find_part_for_description
except Exception:
    check_items_availability = None
    find_part_for_description = None


def fix(invoice_number, dry_run=False):
    inv = Invoice.objects.filter(invoice_number=invoice_number).first()
    if not inv:
        print('Invoice not found:', invoice_number)
        return
    print('Found invoice:', inv.id, inv.invoice_number, 'amount=', float(inv.amount))
    items = list(inv.items.all())
    print('Existing InvoiceItem count:', len(items))
    mrs = list(inv.maintenance_records.all())
    print('Linked MaintenanceRecord count:', len(mrs))

    # build totals counters
    from collections import Counter
    mr_totals = [float(getattr(m, 'price', 0) or 0) for m in mrs]
    ii_totals = [float(getattr(ii, 'total', 0) or 0) for ii in items]
    mr_count = Counter(mr_totals)
    ii_count = Counter(ii_totals)

    created = 0
    candidates = []
    existing_map = {}
    # build existing_items_map by normalized description -> qty
    try:
        for ex in InvoiceItem.objects.filter(invoice=inv):
            k = (ex.description or '').strip().lower()
            try:
                existing_map[k] = existing_map.get(k, Decimal('0')) + Decimal(str(ex.quantity or 0))
            except Exception:
                existing_map[k] = existing_map.get(k, Decimal('0'))
    except Exception:
        existing_map = {}

    for mr in mrs:
        amt = float(getattr(mr, 'price', 0) or 0)
        # if there are fewer invoice items with this amount than maintenance records, plan to create one
        if ii_count.get(amt, 0) < mr_count.get(amt, 0):
            desc = (getattr(getattr(mr, 'service', None), 'name', None) or (mr.notes or '')).strip()
            if not desc:
                # fallback to amount-based description
                desc = f'Service {mr.id} ({amt})'
            # candidate uses qty=1
            candidates.append({'mr': mr, 'description': desc, 'qty': Decimal('1'), 'rate': Decimal(str(amt))})

    # If we have candidates, run availability check (if helper available)
    if candidates and check_items_availability:
        check_list = [{'description': c['description'], 'qty': c['qty']} for c in candidates]
        shortages = check_items_availability(check_list, existing_map)
        if shortages:
            print('Availability shortages detected:')
            for s in shortages:
                p = s[0] if s and s[0] else None
                print(' -', getattr(p, 'name', str(p)), 'available=', s[1], 'requested=', s[2])
            if dry_run:
                print('Dry-run mode: would abort on shortages (no changes made).')
            else:
                print('Aborting due to shortages. No changes applied.')
                return

    # If dry-run, just report planned creations
    if dry_run:
        print('Dry-run: planned InvoiceItem creations:')
        for c in candidates:
            print(f" - MR {getattr(c['mr'],'id',None)} -> description='{c['description']}' qty={c['qty']} rate={c['rate']}")
        print('Dry-run complete. No DB changes applied.')
        return

    # Perform actual creation inside a transaction with select_for_update on involved parts
    try:
        part_ids = set()
        if find_part_for_description:
            for c in candidates:
                try:
                    p = find_part_for_description(c['description'])
                    if p and getattr(p, 'track_stock', False):
                        part_ids.add(p.id)
                except Exception:
                    continue

        with transaction.atomic():
            try:
                if part_ids:
                    from inventory.models import Part
                    Part.objects.select_for_update().filter(id__in=list(part_ids))
            except Exception:
                pass

            for c in candidates:
                try:
                    InvoiceItem.objects.create(
                        invoice=inv,
                        service=getattr(c['mr'], 'service', None),
                        description=c['description'],
                        quantity=float(c['qty']),
                        rate=float(c['rate']),
                        discount=0,
                        total=float(c['rate'])
                    )
                    created += 1
                    print('Created InvoiceItem for MR', getattr(c['mr'], 'id', None), 'amt=', float(c['rate']))
                except Exception as e:
                    print('Failed to create InvoiceItem for MR', getattr(c['mr'], 'id', None), 'err=', e)
    except Exception as e:
        print('Error while creating items, rolling back:', e)
        return

    # recompute invoice amount from items
    s = inv.items.aggregate(total=Sum('total'))['total'] or 0
    inv.amount = float(s)
    inv.save()
    print('Created items:', created)
    print('New invoice.amount =', float(inv.amount))

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Fix invoice by adding missing InvoiceItem rows from linked MaintenanceRecord entries.')
    parser.add_argument('invoice_number', help='Invoice number to fix')
    parser.add_argument('--dry-run', action='store_true', help='Show planned changes without writing to DB')
    args = parser.parse_args()

    fix(args.invoice_number, dry_run=args.dry_run)
