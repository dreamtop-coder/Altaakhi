from decimal import Decimal
from django.db import transaction
import logging
from inventory.models import Supplier, Part
from .models import Bill, BillLine

logger = logging.getLogger('bills')


def migrate_session_bill(session_bill, dry_run=False):
    """Migrate a single session-stored bill dict into persistent Bill/BillLine.

    Returns (bill, None) on success or (None, reason_str) on failure.

    Reasons: 'no_number', 'exists', 'no_supplier', 'missing_part', 'invalid_items', 'error'
    """
    try:
        # normalize keys
        bill_number = session_bill.get('number') or session_bill.get('bill_number')
        if not bill_number:
            return (None, 'no_number')
        # idempotent: skip if exists
        if Bill.objects.filter(bill_number=bill_number).exists():
            return (None, 'exists')

        # supplier: prefer id if present
        supplier = None
        sup_id = session_bill.get('vendor_id') or session_bill.get('supplier_id')
        if sup_id:
            try:
                supplier = Supplier.objects.filter(pk=int(sup_id)).first()
            except Exception:
                supplier = None
        if not supplier:
            name = session_bill.get('vendor_name') or session_bill.get('supplier')
            if name:
                supplier = Supplier.objects.filter(name__iexact=name).first()
        if not supplier:
            return (None, 'no_supplier')

        items = session_bill.get('items') or []
        # allow migration of bills that have no item lines but include an overall amount
        if not isinstance(items, list) or len(items) == 0:
            # try to fallback to overall amount present in session
            amt_raw = session_bill.get('amount') or session_bill.get('grand_total') or session_bill.get('total') or session_bill.get('balance_due')
            if amt_raw is None:
                return (None, 'invalid_items')
            try:
                overall_amt = Decimal(str(amt_raw))
            except Exception:
                return (None, 'invalid_items')

        # parse lines and verify parts
        parsed_lines = []
        subtotal = Decimal('0')
        total_discount = Decimal('0')
        grand_total = Decimal('0')
        for it in items:
            desc = (it.get('description') or '').strip()
            try:
                q = Decimal(str(it.get('qty') or '0'))
                r = Decimal(str(it.get('rate') or '0'))
                d = Decimal(str(it.get('discount') or '0'))
            except Exception:
                return (None, 'invalid_items')
            # find part
            part = None
            if desc:
                part = Part.objects.filter(name__iexact=desc).first()
                if not part:
                    part = Part.objects.filter(code__iexact=desc).first()
            if not part:
                return (None, f'missing_part:{desc}')
            line_total = q * r
            line_net = (q * r * (Decimal('1') - (d / Decimal('100')))).quantize(Decimal('0.001'))
            discount_amount = (line_total - line_net).quantize(Decimal('0.001'))
            subtotal += line_total
            total_discount += discount_amount
            grand_total += line_net
            parsed_lines.append({'part': part, 'description': desc, 'qty': q, 'rate': r, 'discount': d, 'account_type': (it.get('account_type') or 'inventory'), 'line_amount': line_net})

        # create bill and lines in atomic transaction
        with transaction.atomic():
            # lock supplier and parts rows to avoid races
            part_ids = [ld['part'].pk for ld in parsed_lines]
            if supplier and not dry_run:
                supplier = Supplier.objects.select_for_update().filter(pk=supplier.pk).first()
            if part_ids and not dry_run:
                list(Part.objects.select_for_update().filter(pk__in=part_ids))
            # if parsed_lines empty but overall_amt present, use overall_amt as grand_total
            if len(parsed_lines) == 0:
                subtotal_val = overall_amt
                discount_val = Decimal('0')
                grand_val = overall_amt
            else:
                subtotal_val = subtotal
                discount_val = total_discount
                grand_val = grand_total
            if dry_run:
                # return a planned summary for dry-run (truthy)
                planned = {'bill_number': bill_number, 'lines': parsed_lines, 'grand_total': grand_val}
                return (planned, None)

            bill = Bill.objects.create(
                bill_number=bill_number,
                supplier=supplier,
                bill_date=session_bill.get('date') or None,
                notes=session_bill.get('notes') or session_bill.get('subject') or '',
                subtotal=subtotal_val.quantize(Decimal('0.001')),
                discount_total=discount_val.quantize(Decimal('0.001')),
                grand_total=grand_val.quantize(Decimal('0.001')),
                status=(session_bill.get('status', 'sent').lower() if session_bill.get('status') else 'sent'),
            )
            try:
                logger.info(f"Bill migration executed | bill_number={bill.bill_number} | supplier={getattr(supplier,'id',None)} | lines={len(parsed_lines)}")
            except Exception:
                pass
            for ld in parsed_lines:
                bl = BillLine.objects.create(
                    bill=bill,
                    part=ld['part'],
                    description=ld['description'] or '',
                    quantity=ld['qty'],
                    rate=ld['rate'],
                    discount_percent=ld['discount'],
                    account_type=ld.get('account_type', 'inventory'),
                    amount=ld['line_amount'],
                )
                # update part (only update quantity for stock-tracked parts)
                try:
                    p = ld['part']
                    p.purchase_price = ld['rate']
                    # increment integer quantity for purchases (always increase)
                    try:
                        qn = int(float(ld['qty']))
                        if qn > 0:
                            p.quantity = (p.quantity or 0) + qn
                    except Exception:
                        pass
                    p.supplier = supplier
                    p.save()
                except Exception:
                    # if part update fails, rollback
                    raise
            # update supplier balance
            if bill.status != 'draft' and grand_val and grand_val != Decimal('0'):
                supplier.amount = (supplier.amount or Decimal('0')) + grand_val
                supplier.save()
        return (bill, None)
    except Exception as e:
        return (None, 'error:' + str(e))
