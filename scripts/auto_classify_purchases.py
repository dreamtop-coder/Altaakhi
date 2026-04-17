import os, sys, re
os.environ.setdefault('DJANGO_SETTINGS_MODULE','workshop.settings')
# ensure project root on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
django.setup()
from bills.models import BillLine
from inventory.models import Part
from django.db import transaction

# keywords (lowercased) — tune these as needed
EXPENSE_KEYWORDS = ['حديد','أدوات','tool','tools','iron','paint','مصروف','أدوات']
INVENTORY_KEYWORDS = ['فلتر','زيت','قطع','قطع غيار','spare','filter','oil','part','parts','spare part']

def contains_keyword(text, keywords):
    if not text:
        return False
    t = text.lower()
    for k in keywords:
        if k in t:
            return True
    return False

@transaction.atomic
def classify_billlines(dry_run=True):
    lines = BillLine.objects.select_related('part').all()
    changed = 0
    for ln in lines:
        desc = (ln.description or '')
        part_name = (ln.part.name if ln.part else '')
        # decide
        decision = None
        # expense keywords first
        if contains_keyword(desc, EXPENSE_KEYWORDS) or contains_keyword(part_name, EXPENSE_KEYWORDS):
            decision = 'expense'
        elif contains_keyword(desc, INVENTORY_KEYWORDS) or contains_keyword(part_name, INVENTORY_KEYWORDS):
            decision = 'inventory'
        else:
            # leave as default
            decision = None
        if decision and ln.account_type != decision:
            print(f"Line {ln.id}: setting account_type {ln.account_type} -> {decision} (desc='{desc[:40]}')")
            if not dry_run:
                ln.account_type = decision
                ln.save()
            changed += 1
    print(f"Processed {lines.count()} lines; matches to change: {changed}")

@transaction.atomic
def classify_parts(dry_run=True):
    parts = Part.objects.all()
    changed = 0
    for p in parts:
        name = (p.name or '')
        decision = None
        if contains_keyword(name, EXPENSE_KEYWORDS):
            decision = False
        elif contains_keyword(name, INVENTORY_KEYWORDS):
            decision = True
        if decision is not None and bool(p.is_inventory) != bool(decision):
            print(f"Part {p.id} ('{p.name}'): is_inventory {p.is_inventory} -> {decision}")
            if not dry_run:
                p.is_inventory = bool(decision)
                p.save()
            changed += 1
    print(f"Processed {parts.count()} parts; matches to change: {changed}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Auto-classify BillLine and Part inventory vs expense by keywords')
    parser.add_argument('--apply', action='store_true', help='Apply changes (default is dry-run)')
    args = parser.parse_args()
    print('Running auto-classify (dry-run={})'.format(not args.apply))
    classify_parts(dry_run=not args.apply)
    classify_billlines(dry_run=not args.apply)
    print('Done')
