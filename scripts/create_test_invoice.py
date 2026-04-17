#!/usr/bin/env python
"""Create a small test Invoice linked to a Part so COGS appears in financials.

Creates or updates a Part named 'Test Part for COGS' with a purchase_price and
is_inventory=True. Creates a Client (TEST-CLIENT-1) if missing, then creates an
Invoice and one InvoiceItem whose description matches the Part name so
`find_part_for_description` resolves it.

Run with the project's Python (virtualenv):
  .venv\Scripts\python.exe scripts/create_test_invoice.py
"""
import os
import sys
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
# Ensure project root is on sys.path so Django settings package can be imported
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
import django
django.setup()

def main():
    try:
        from inventory.models import Part
        from clients.models import Client
        from invoices.models import Invoice, InvoiceItem
    except Exception as e:
        print('Failed importing models:', e)
        sys.exit(1)

    # Ensure a Part exists with purchase_price and is_inventory=True
    part_name = 'Test Part for COGS'
    p_defaults = {
        'purchase_price': Decimal('20.00'),
        'is_inventory': True,
    }
    part, created = Part.objects.get_or_create(name=part_name, defaults=p_defaults)
    if not created:
        # enforce desired defaults
        changed = False
        try:
            if getattr(part, 'purchase_price', None) != p_defaults['purchase_price']:
                part.purchase_price = p_defaults['purchase_price']
                changed = True
        except Exception:
            part.purchase_price = p_defaults['purchase_price']
            changed = True
        try:
            if getattr(part, 'is_inventory', True) is not True:
                part.is_inventory = True
                changed = True
        except Exception:
            part.is_inventory = True
            changed = True
        if changed:
            part.save()

    # Ensure a Client exists
    client, _ = Client.objects.get_or_create(
        customer_id='TEST-CLIENT-1',
        defaults={'first_name': 'TestClient', 'phone_number': '000'},
    )

    # Create an Invoice with a unique invoice_number
    import time
    invoice_number = f"INV-TEST-{int(time.time())}"
    inv = Invoice.objects.create(invoice_number=invoice_number, client=client, amount=0, paid=False)

    # Create one InvoiceItem whose description exactly matches the Part name
    qty = Decimal('2')
    rate = Decimal('50.00')
    total = (qty * rate)
    InvoiceItem.objects.create(invoice=inv, description=part.name, quantity=qty, rate=rate, total=total)

    # Recalculate invoice amount
    try:
        inv.recalc_amount()
    except Exception:
        inv.amount = total
        inv.save()

    print('Created invoice:', inv.id, inv.invoice_number, 'amount=', float(inv.amount))
    print('Part id:', part.id, 'purchase_price=', float(part.purchase_price))

if __name__ == '__main__':
    main()
