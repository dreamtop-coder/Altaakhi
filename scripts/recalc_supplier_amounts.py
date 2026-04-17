#!/usr/bin/env python
"""Recalculate Supplier.amount from persistent Bill records.

Run from project root using the project's Python virtualenv:
  .venv\Scripts\python.exe scripts\recalc_supplier_amounts.py

This will set each Supplier.amount = SUM(Bill.grand_total) for that supplier.
It prints a summary of changes.
"""
import os
import sys
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import django
django.setup()

from inventory.models import Supplier
from bills.models import Bill


def recalc():
    suppliers = Supplier.objects.all()
    total_changed = 0
    for s in suppliers:
        # sum grand_total of bills for this supplier
        qs = Bill.objects.filter(supplier=s)
        sum_amt = Decimal('0')
        for b in qs:
            try:
                sum_amt += Decimal(str(getattr(b, 'grand_total', '0') or '0'))
            except Exception:
                continue
        # normalize to 3 decimal places like other code uses
        sum_amt = sum_amt.quantize(Decimal('0.001'))
        prev = s.amount or Decimal('0')
        if prev != sum_amt:
            print(f"Supplier ID={s.id} '{s.name}': {prev} -> {sum_amt}")
            s.amount = sum_amt
            s.save()
            total_changed += 1

    print(f"Recalculated supplier amounts. Suppliers changed: {total_changed}")


if __name__ == '__main__':
    recalc()
