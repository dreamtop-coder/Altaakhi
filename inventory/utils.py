from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class InventoryShortage(Exception):
    pass


def find_part_for_description(desc):
    """Try to resolve a Part by description using exact, contains, then token match.

    Returns Part instance or None.
    """
    if not desc:
        return None
    from .models import Part
    try:
        p = Part.objects.filter(name__iexact=desc).first()
        if p:
            return p
    except Exception:
        p = None
    try:
        p = Part.objects.filter(name__icontains=desc).first()
        if p:
            return p
    except Exception:
        p = None
    tokens = [t.strip() for t in desc.split() if t.strip()]
    for t in tokens:
        try:
            p = Part.objects.filter(name__icontains=t).first()
            if p:
                return p
        except Exception:
            continue
    return None


def check_items_availability(items, existing_map=None):
    """Check availability for a list of item dicts.

    items: [{'description':..., 'qty': <number>}, ...]
    existing_map: mapping of normalized description -> Decimal already_included (optional)

    Returns list of shortages as tuples (part, available, requested) or empty list.
    """
    from .models import Part
    shortages = []
    try:
        for it in items:
            desc = (it.get('description') or '').strip()
            if not desc:
                continue
            try:
                req_q = Decimal(str(it.get('qty') or 0))
            except Exception:
                req_q = Decimal('0')
            if req_q <= 0:
                continue
            part = find_part_for_description(desc)
            # If part is found but not tracked, skip availability enforcement
            try:
                if part and not getattr(part, 'track_stock', False):
                    continue
            except Exception:
                pass
            if not part:
                continue
            cur_qty = Decimal(str(part.quantity or 0))
            already = Decimal('0')
            try:
                if existing_map:
                    already = Decimal(str(existing_map.get(desc.lower(), 0) or 0))
            except Exception:
                already = Decimal('0')
            available = cur_qty - already
            if available < Decimal('0'):
                available = Decimal('0')
            if req_q > available:
                shortages.append((part, available, req_q))
    except Exception:
        # On unexpected error, return a generic shortage to force caller to be conservative
        return [('', Decimal('0'), Decimal('1'))]
    return shortages


def apply_inventory_changes_for_invoice(items, decrement=True):
    """Apply inventory changes for invoice-like items.

    If decrement=True then decrease Part.quantity by each item's qty (used when selling).
    If decrement=False then increase Part.quantity by each item's qty.
    """
    from .models import Part
    from decimal import Decimal
    from django.db import transaction
    # Use a DB transaction and row-level locks to avoid race conditions
    with transaction.atomic():
        for it in items:
            desc = (it.get('description') or '').strip()
            if not desc:
                continue
            try:
                qty = Decimal(str(it.get('qty') or 0))
            except Exception:
                qty = Decimal('0')
            if qty == 0:
                continue
            part = find_part_for_description(desc)
            # If part is found but not tracked, do not apply inventory changes
            try:
                if part and not getattr(part, 'track_stock', False):
                    continue
            except Exception:
                pass
            if not part:
                continue
            try:
                # round to integer where system expects integer stock
                delta = int(qty.to_integral_value())
            except Exception:
                try:
                    delta = int(float(qty))
                except Exception:
                    delta = 0
            if delta == 0:
                continue
            # re-fetch the part row with a SELECT FOR UPDATE lock
            try:
                part = Part.objects.select_for_update().get(pk=part.pk)
                try:
                    logger.info(f"Lock acquired for part {part.pk}")
                except Exception:
                    pass
            except Exception:
                # if re-fetch fails, skip this line to avoid partial updates
                continue
            if decrement:
                new_q = (part.quantity or 0) - delta
                if new_q < 0:
                    new_q = 0
                part.quantity = new_q
            else:
                part.quantity = (part.quantity or 0) + delta
            try:
                op = '-' if decrement else '+'
                logger.info(f"Stock change | part={part.pk} | delta={op}{delta} | new={part.quantity}")
            except Exception:
                pass
            part.save()
