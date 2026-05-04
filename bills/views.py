from django.shortcuts import render, redirect
import logging
from django.contrib import messages
from django.http import Http404
import json
from decimal import Decimal, ROUND_HALF_UP

from .models import Bill, BillLine
from .models import BillPayment
from inventory.models import Supplier, Part
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Sum
from decimal import Decimal
from .services import migrate_session_bill

# bills module logger
logger = logging.getLogger('bills')


def add_bill(request):
    # Handle POST to create persistent Bill + lines and update inventory/supplier
    if request.method == 'POST':
        bill_number = request.POST.get('bill_number') or request.POST.get('number')
        bill_date = request.POST.get('bill_date')
        supplier_id = request.POST.get('selected_supplier_id')
        account_val = request.POST.get('account')
        items_json = request.POST.get('items_json') or request.POST.get('items')
        action = request.POST.get('action', 'save')

        items = []
        try:
            items = json.loads(items_json) if items_json else []
        except Exception:
            items = []

        subtotal = Decimal('0')
        discount_total = Decimal('0')

        # validate required fields for non-draft saves
        if action != 'save_draft':
            if not supplier_id:
                messages.error(request, 'Please select a vendor')
                return redirect('/bills/add/')
            if not account_val:
                # If account not provided, fall back to supplier id to satisfy validation.
                # The `account` value is not otherwise used later, so prefer supplier id.
                account_val = supplier_id or ''

        # compute totals server-side and prepare lines
        lines = []
        for it in items:
            try:
                qty = Decimal(str(it.get('qty') or it.get('quantity') or '0'))
                rate = Decimal(str(it.get('rate') or it.get('price') or '0'))
                disc = Decimal(str(it.get('discount') or it.get('discount_percent') or '0'))
                line_total = qty * rate
                line_net = (qty * rate * (Decimal('1') - (disc / Decimal('100'))))
                subtotal += line_total
                discount_total += (line_total - line_net)
                # Force account_type to 'inventory' for bills (purchase stock only)
                lines.append({
                    'description': it.get('description') or it.get('item') or '',
                    'qty': qty,
                    'rate': rate,
                    'discount': disc,
                    'account_type': 'inventory',
                    'amount': line_net
                })
            except Exception:
                # skip malformed line entries but continue processing others
                pass
        # For purchase bills we do not perform inventory availability checks here.
        # Bills represent incoming stock (purchases) and will increase Part.quantity
        # when saved. Any inventory validation for sales is handled elsewhere.

        # Determine if this is an update to an existing bill
        # compute grand total used for both update and create branches
        grand = subtotal - discount_total

        supplier = None
        try:
            if supplier_id:
                supplier = Supplier.objects.filter(pk=int(supplier_id)).first()
        except Exception:
            supplier = None

        bill_id = request.POST.get('bill_id')
        try:
            if bill_id:
                # Update existing bill inside a transaction (revert old effects, apply new)
                with transaction.atomic():
                    existing = Bill.objects.select_related('supplier').prefetch_related('lines').get(pk=int(bill_id))
                    old_grand = existing.grand_total or Decimal('0')
                    old_supplier = existing.supplier

                    # Ensure bill_number uniqueness when changing
                    try:
                        if bill_number and bill_number != getattr(existing, 'bill_number', ''):
                            if Bill.objects.filter(bill_number=bill_number).exclude(pk=existing.id).exists():
                                import re
                                m = re.match(r'^(.*?)(\d+)$', bill_number)
                                if m:
                                    prefix = m.group(1)
                                    num_str = m.group(2)
                                    width = len(num_str)
                                    try:
                                        base = int(num_str)
                                    except Exception:
                                        base = None
                                    if base is not None:
                                        for i in range(1, 1000000):
                                            candidate = f"{prefix}{base + i:0{width}d}"
                                            if not Bill.objects.filter(bill_number=candidate).exists():
                                                bill_number = candidate
                                                break
                                else:
                                    original = bill_number
                                    for i in range(1, 1000000):
                                        candidate = f"{original}-{i}"
                                        if not Bill.objects.filter(bill_number=candidate).exists():
                                            bill_number = candidate
                                            break
                    except Exception:
                        pass

                    # update bill fields
                    existing.bill_number = bill_number or getattr(existing, 'bill_number', '')
                    existing.supplier = supplier
                    existing.bill_date = bill_date or None
                    existing.notes = request.POST.get('notes', '')
                    existing.subtotal = subtotal.quantize(Decimal('0.001'))
                    existing.discount_total = discount_total.quantize(Decimal('0.001'))
                    existing.grand_total = grand.quantize(Decimal('0.001'))
                    existing.status = 'sent' if action == 'save_send' else 'saved'
                    existing.save()

                    # revert old part quantities and delete old lines
                    try:
                        for old_ln in existing.lines.all():
                            try:
                                part = Part.objects.select_for_update().filter(name__iexact=old_ln.description).first()
                                if part:
                                    try:
                                        dec_q = Decimal(str(old_ln.quantity or 0))
                                        delta = int(dec_q.to_integral_value(rounding=ROUND_HALF_UP))
                                    except Exception:
                                        delta = int(old_ln.quantity or 0)
                                    old_qty = part.quantity or 0
                                    part.quantity = (part.quantity or 0) - delta
                                    if part.quantity < 0:
                                        part.quantity = 0
                                    part.save()
                                    try:
                                        logger.info(f"Stock reverted | part={part.id} | delta=-{delta} | old_qty={old_qty} | new_qty={part.quantity} | bill_update={existing.id}")
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                        existing.lines.all().delete()
                    except Exception:
                        pass

                    # create new lines and update parts
                    for ln in lines:
                        # Ensure account_type is inventory regardless of incoming data
                        BillLine.objects.create(
                            bill=existing,
                            description=ln['description'],
                            quantity=ln['qty'],
                            rate=ln['rate'],
                            discount_percent=ln['discount'],
                            account_type='inventory',
                            amount=ln['amount']
                        )
                        try:
                            part = Part.objects.select_for_update().filter(name__iexact=ln['description']).first()
                            if part:
                                # set purchase_price only when rate is meaningful
                                try:
                                    rate_val = Decimal(str(ln['rate']))
                                except Exception:
                                    rate_val = None
                                if rate_val and rate_val != Decimal('0'):
                                    part.purchase_price = rate_val
                                try:
                                    dec_q = Decimal(str(ln['qty'] or 0))
                                    add_q = int(dec_q.to_integral_value(rounding=ROUND_HALF_UP))
                                except Exception:
                                    add_q = int(ln['qty'] or 0)
                                part.quantity = (part.quantity or 0) + add_q
                                part.save()
                        except Exception:
                            pass

                    # adjust supplier balances: subtract old, add new (skip for drafts)
                    try:
                        if old_supplier and action != 'save_draft':
                            old_supplier.amount = (old_supplier.amount or Decimal('0')) - (old_grand or Decimal('0'))
                            old_supplier.save()
                    except Exception:
                        pass
                    try:
                        if supplier and action != 'save_draft':
                            supplier.amount = (supplier.amount or Decimal('0')) + grand.quantize(Decimal('0.001'))
                            supplier.save()
                    except Exception:
                        pass

                    return redirect(f'/bills/view/{existing.id}/')
        except Bill.DoesNotExist:
            # fall through to create a new bill if the provided id is invalid
            pass
        except Exception as ex:
            # Log unexpected exceptions so we can debug why update branch failed
            try:
                import logging
                logging.exception('Error updating existing Bill (falling back to create-new): %s', ex)
            except Exception:
                pass
            # fall through to create branch
            pass
        

        # create Bill and lines (create-new branch)
        # Ensure bill_number is unique to avoid DB integrity errors
        try:
            from django.db import IntegrityError
            if not bill_number:
                # generate next bill number using existing pattern
                last = Bill.objects.order_by('-id').first()
                if last and getattr(last, 'bill_number', None):
                    import re
                    m = re.match(r'^(.*?)(\d+)$', last.bill_number)
                    if m:
                        prefix = m.group(1)
                        num_str = m.group(2)
                        width = len(num_str)
                        try:
                            num = int(num_str) + 1
                            bill_number = f"{prefix}{num:0{width}d}"
                        except Exception:
                            bill_number = ''
                    else:
                        bill_number = ''
                else:
                    bill_number = ''
            # If a bill_number was provided and already exists, allow the
            # database unique constraint to raise IntegrityError so callers/tests
            # can detect duplicates. We only auto-generate numbers when none
            # was provided by the client.
        except Exception:
            # best-effort: leave bill_number as-is and let DB raise if still collides
            pass

        # create Bill and lines inside an atomic transaction, then update inventory/supplier
        try:
            from inventory.utils import apply_inventory_changes_for_invoice
            from django.db import IntegrityError as _IntegrityError
            with transaction.atomic():
                # If client provided a bill_number that already exists, let the
                # database/transaction caller observe IntegrityError instead
                # of silently auto-incrementing. Tests expect IntegrityError.
                from django.db import IntegrityError as _IntegrityError
                if bill_number and Bill.objects.filter(bill_number=bill_number).exists():
                    raise _IntegrityError('duplicate bill_number')

                bill = Bill.objects.create(
                    bill_number=bill_number or '',
                    supplier=supplier,
                    bill_date=bill_date or None,
                    notes=request.POST.get('notes', ''),
                    subtotal=subtotal.quantize(Decimal('0.001')),
                    discount_total=discount_total.quantize(Decimal('0.001')),
                    grand_total=grand.quantize(Decimal('0.001')),
                    status='sent' if action == 'save_send' else 'saved'
                )
                try:
                    logger.info(f"Bill created | user={getattr(request, 'user', None)} | bill={bill.bill_number} | items={len(lines)} | supplier={getattr(supplier, 'id', None)}")
                except Exception:
                    pass

                for ln in lines:
                    # Persist lines as inventory-only
                    BillLine.objects.create(
                        bill=bill,
                        description=ln['description'],
                        quantity=ln['qty'],
                        rate=ln['rate'],
                        discount_percent=ln['discount'],
                        account_type='inventory',
                        amount=ln['amount']
                    )

                # Update Part purchase_price from provided rate when meaningful.
                # We do NOT change quantities here; `apply_inventory_changes_for_invoice`
                # will perform quantity updates in one place to avoid duplication.
                try:
                    for ln in lines:
                        try:
                            rate_val = Decimal(str(ln.get('rate') or '0'))
                        except Exception:
                            rate_val = Decimal('0')
                        if rate_val and rate_val != Decimal('0'):
                            try:
                                part = Part.objects.filter(name__iexact=ln.get('description') or '').first()
                                if part:
                                    part.purchase_price = rate_val
                                    part.save()
                            except Exception:
                                pass
                except Exception:
                    pass

                # update parts quantities and purchase_price from lines
                try:
                    for ln in lines:
                        try:
                            desc = ln.get('description') or ''
                            part = Part.objects.select_for_update().filter(name__iexact=desc).first()
                            if not part:
                                continue
                            # update purchase price if meaningful
                            try:
                                rate_val = Decimal(str(ln.get('rate') or '0'))
                            except Exception:
                                rate_val = Decimal('0')
                            if rate_val and rate_val != Decimal('0'):
                                part.purchase_price = rate_val
                            # increase quantity (purchase)
                            try:
                                dec_q = Decimal(str(ln.get('qty') or ln.get('quantity') or 0))
                                add_q = int(dec_q.to_integral_value(rounding=ROUND_HALF_UP))
                            except Exception:
                                add_q = int(ln.get('qty') or ln.get('quantity') or 0)
                            part.quantity = (part.quantity or 0) + add_q
                            part.save()
                        except Exception:
                            pass
                except Exception:
                    # if inventory update fails, rollback transaction
                    raise

                # update supplier balance unless saving as draft
                try:
                    if supplier and action != 'save_draft':
                        supplier.amount = (supplier.amount or Decimal('0')) + grand.quantize(Decimal('0.001'))
                        supplier.save()
                except Exception:
                    # let transaction handle errors if supplier save fails
                    raise

            return redirect(f'/bills/view/{bill.id}/')
        except _IntegrityError:
            # Let IntegrityError bubble up so callers/tests can detect duplicates
            raise
        except Exception:
            # surface a friendly error and avoid partially applied state
            try:
                messages.error(request, 'فشل في إنشاء الفاتورة. حاول لاحقاً.')
            except Exception:
                pass
            return redirect('/bills/add/')

    # Provide suppliers sample data for client-side suggestions
    suppliers = Supplier.objects.all().order_by('-id')[:200]
    suppliers_sample = []
    for s in suppliers:
        suppliers_sample.append({'id': s.id, 'name': s.name, 'phone': getattr(s, 'phone', ''), 'addresses': [s.address] if getattr(s, 'address', None) else []})
    # compute next bill number (preserve existing prefix and width when possible)
    next_bill_number = 'BIL-000001'
    try:
        last = Bill.objects.order_by('-id').first()
        if last and getattr(last, 'bill_number', None):
            import re
            m = re.match(r'^(.*?)(\d+)$', last.bill_number)
            if m:
                prefix = m.group(1)
                num_str = m.group(2)
                width = len(num_str)
                try:
                    num = int(num_str) + 1
                    next_bill_number = f"{prefix}{num:0{width}d}"
                except Exception:
                    pass
    except Exception:
        pass

    return render(request, 'bills_add.html', {'suppliers_sample': suppliers_sample, 'next_bill_number': next_bill_number})


def bills_list(request):
    """Render bills listing page using persistent Bill model when available.
    Returns a list of dicts matching the expected template keys for backward compatibility.
    """
    bills_qs = Bill.objects.select_related('supplier').all().order_by('-bill_date', '-created_at')
    bills = []
    for b in bills_qs:
        bills.append({
            'id': b.id,
            'date': getattr(b, 'bill_date', ''),
            'number': getattr(b, 'bill_number', ''),
            'vendor_name': b.supplier.name if b.supplier else '',
            'status': b.status,
            'due_date': '',
            'amount': getattr(b, 'grand_total', ''),
            'balance_due': getattr(b, 'grand_total', ''),
        })
    # also include recent session bills for compatibility (optional)
    session_bills = request.session.get('recent_bills', []) or []
    # append session bills with an explicit session_index so template can link correctly
    for idx, sb in enumerate(session_bills):
        bills.append({
            # no 'id' to mark as session-only
            'session_index': idx,
            'date': sb.get('date') or sb.get('bill_date') or '',
            'number': sb.get('number') or sb.get('bill_number') or '',
            'vendor_name': sb.get('vendor_name') or sb.get('supplier_name') or sb.get('supplier') or '',
            'status': sb.get('status', ''),
            'due_date': sb.get('due_date', ''),
            'amount': sb.get('grand_total') or sb.get('amount') or '',
            'balance_due': sb.get('balance_due') or sb.get('amount') or '',
        })
    # Pagination / per-page options (match suppliers list behaviour)
    per_page_options = [25, 50, 100, 200, 'all']
    per_page_raw = request.GET.get('per_page', '25')
    page_obj = None
    try:
        if str(per_page_raw).lower() == 'all':
            per_page_for_template = 0
            # no pagination, show all
            per_page_value = None
            page_obj = None
        else:
            per_page_value = int(per_page_raw)
            per_page_for_template = per_page_value
    except Exception:
        per_page_value = 25
        per_page_for_template = 25

    if per_page_value:
        paginator = Paginator(bills, per_page_value)
        page_num = request.GET.get('page', 1)
        try:
            page_obj = paginator.page(page_num)
        except (PageNotAnInteger, EmptyPage):
            page_obj = paginator.page(1)
        bills_page = list(page_obj.object_list)
    else:
        bills_page = bills

    return render(request, 'bills_list.html', {
        'bills': bills_page,
        'per_page': per_page_for_template,
        'per_page_options': per_page_options,
        'page_obj': page_obj,
    })


@require_GET
def supplier_bills_json(request):
    """Return outstanding bills for a supplier (used by vendor-payments add page)."""
    sid = request.GET.get('id') or request.GET.get('supplier_id')
    out = []
    if not sid:
        return JsonResponse(out, safe=False)
    try:
        s = Supplier.objects.get(pk=int(sid))
    except Exception:
        return JsonResponse(out, safe=False)

    try:
        bills_qs = Bill.objects.filter(supplier=s).order_by('bill_date')
        from django.db.models import Sum
        for b in bills_qs:
            paid = BillPayment.objects.filter(bill=b, status='paid').aggregate(total=Sum('amount'))['total'] or 0
            try:
                grand = float(b.grand_total or 0)
            except Exception:
                grand = 0.0
            try:
                paid_f = float(paid or 0)
            except Exception:
                paid_f = 0.0
            remaining = max(0.0, grand - paid_f)
            # include keys compatible with invoices payments JS (invoice_number)
            out.append({
                'id': b.id,
                'bill_number': b.bill_number,
                'invoice_number': b.bill_number,
                'date': getattr(b, 'bill_date', ''),
                'amount': grand,
                'paid': paid_f,
                'remaining': remaining
            })
    except Exception as e:
        # If DB tables/migrations are missing (or other DB errors), avoid returning HTTP 500
        # and provide an empty list so the frontend can continue to function.
        try:
            import logging
            logging.exception('supplier_bills_json error')
        except Exception:
            pass
        return JsonResponse(out, safe=False)
    return JsonResponse(out, safe=False)


@login_required
def vendor_payments_list(request):
    """List supplier payments (BillPayment records)."""
    payments_qs = BillPayment.objects.select_related('supplier', 'bill').all().order_by('-payment_date')
    payments = []
    for p in payments_qs:
        payments.append({
            'id': p.id,
            'supplier_name': p.supplier.name if p.supplier else '',
            'payment_date': p.payment_date,
            'reference': p.reference,
            'method': p.get_method_display() if hasattr(p, 'get_method_display') else p.method,
            'status': p.get_status_display() if hasattr(p, 'get_status_display') else p.status,
            'amount': float(p.amount or 0),
        })
    return render(request, 'vendor_payments_list.html', {'payments': payments, 'per_page': 25, 'per_page_options': [25,50,100,200,'all'], 'page_obj': None})


@login_required
def add_vendor_payment(request):
    """Render add vendor payment page and handle POST to create BillPayment records."""
    from django.http import JsonResponse, HttpResponseBadRequest
    from decimal import Decimal
    from django.utils import timezone

    if request.method == 'POST':
        supplier_id = request.POST.get('supplier_id')
        payment_date = request.POST.get('payment_date')
        method = request.POST.get('method')
        reference = request.POST.get('reference')
        notes = request.POST.get('notes')
        allocations = request.POST.get('allocations')
        try:
            import json
            alloc = json.loads(allocations or '[]')
        except Exception:
            alloc = []

        try:
            supplier = Supplier.objects.get(id=int(supplier_id))
        except Exception:
            return HttpResponseBadRequest('Supplier not found')

        draft_flag = request.POST.get('draft') in ('1', 'true', 'yes') or request.POST.get('action') == 'save_draft'
        created = []
        try:
            for a in alloc:
                bill_id = a.get('bill_id')
                amt = a.get('amount')
                try:
                    amt_val = Decimal(str(amt or 0))
                except Exception:
                    amt_val = Decimal('0')
                if amt_val <= 0:
                    continue
                bill = None
                try:
                    if bill_id:
                        bill = Bill.objects.get(id=int(bill_id))
                except Exception:
                    bill = None

                bp = BillPayment.objects.create(
                    bill=bill,
                    supplier=supplier,
                    amount=amt_val.quantize(Decimal('0.001')),
                    status=('unpaid' if draft_flag else 'paid'),
                    method=method or 'cash',
                    reference=reference,
                    notes=notes,
                )
                created.append(bp.id)

                # update bill status and supplier balance when not draft
                if not draft_flag and bill:
                    paid_amount = BillPayment.objects.filter(bill=bill, status='paid').aggregate(total=models.Sum('amount'))['total'] or 0
                    try:
                        from decimal import Decimal as D
                        if D(str(paid_amount or 0)) >= D(str(bill.grand_total or 0)) and float(bill.grand_total or 0) > 0:
                            bill.status = 'paid'
                        else:
                            bill.status = bill.status
                        bill.save()
                    except Exception:
                        pass
                if not draft_flag:
                    try:
                        supplier.amount = (supplier.amount or Decimal('0')) - amt_val.quantize(Decimal('0.001'))
                        supplier.save()
                    except Exception:
                        pass
        except Exception as e:
            return HttpResponseBadRequest('Failed to process payments: ' + str(e))

        return JsonResponse({'created': created})

    # GET: render page
    suppliers = list(Supplier.objects.all().order_by('name')[:500])
    # compute next payment reference (e.g. 202600001) using year + sequence
    next_payment_ref = ''
    try:
        last = BillPayment.objects.order_by('-id').first()
        import datetime
        year = datetime.datetime.now().year
        if last and getattr(last, 'reference', None):
            ref = str(last.reference).strip()
            if ref.startswith(str(year)) and ref[len(str(year)):].isdigit():
                try:
                    tail = int(ref[len(str(year)):]) + 1
                    next_payment_ref = f"{year}{tail:06d}"
                except Exception:
                    next_payment_ref = f"{year}000001"
            else:
                import re
                m = re.search(r"(\d+)$", ref)
                if m:
                    try:
                        num = int(m.group(1)) + 1
                        width = len(m.group(1))
                        next_payment_ref = str(num).zfill(width)
                    except Exception:
                        next_payment_ref = f"{year}000001"
                else:
                    next_payment_ref = f"{year}000001"
        else:
            next_payment_ref = f"{year}000001"
    except Exception:
        next_payment_ref = ''

    return render(request, 'vendor_payments_add.html', {'suppliers': suppliers, 'next_payment_ref': next_payment_ref})


def bill_detail(request, bill_id=None, session_index=None):
    """Render bill detail.

    Accepts either a DB `bill_id` (via /bills/view/<id>/) or a session index
    (via /bills/view/session/<index>/). This avoids numeric collisions between
    session indices and DB primary keys.
    """
    session_raw = None

    # If a DB id is provided, prefer it.
    if bill_id is not None:
        try:
            bill = Bill.objects.get(pk=int(bill_id))
        except Exception:
            bill = None

        if bill:
            items = []
            sub = Decimal('0')
            disc = Decimal('0')
            for line in bill.lines.all():
                q = Decimal(str(line.quantity))
                r = Decimal(str(line.rate))
                d = Decimal(str(line.discount_percent))
                line_total = q * r
                line_net = Decimal(str(line.amount))
                sub += line_total
                disc += (line_total - line_net)
                items.append({
                    'description': line.description,
                    'qty': str(line.quantity),
                    'rate': str(line.rate),
                    'discount': str(line.discount_percent),
                    'line_amount': str(line.amount),
                })
            grand = sub - disc
            summary = {
                'sub_total': str(sub.quantize(Decimal('0.001'))),
                'total_discount': str(disc.quantize(Decimal('0.001'))),
                'grand_total': str(grand.quantize(Decimal('0.001'))),
            }
            
            date_iso = bill.bill_date.isoformat() if getattr(bill, 'bill_date', None) else ''
            date_display = bill.bill_date.strftime('%d/%m/%Y') if getattr(bill, 'bill_date', None) else ''
            bill_dict = {
                'id': bill.id,
                'number': bill.bill_number,
                'vendor_name': bill.supplier.name if bill.supplier else '',
                'vendor_id': bill.supplier.id if bill.supplier else '',
                'date': date_iso,
                'date_display': date_display,
                'status': bill.status,
                'items': items,
            }
            return render(request, 'bill_detail.html', {'bill': bill_dict, 'session_raw': None, 'summary': summary})

    # If a session index route was used, render from session (or fallback to DB by number).
    if session_index is not None:
        recent = request.session.get('recent_bills', [])
        if 0 <= session_index < len(recent):
            session_bill = recent[session_index]
            session_raw = session_bill
            items = session_bill.get('items') or []

            # If session bill lacks item details but has a bill number, attempt to load DB bill by number.
            if (not items) and session_bill.get('number'):
                try:
                    db_bill = Bill.objects.get(bill_number=session_bill['number'])
                    items = []
                    sub = Decimal('0')
                    disc = Decimal('0')
                    for line in db_bill.lines.all():
                        q = Decimal(str(line.quantity))
                        r = Decimal(str(line.rate))
                        d = Decimal(str(line.discount_percent))
                        line_total = q * r
                        line_net = Decimal(str(line.amount))
                        sub += line_total
                        disc += (line_total - line_net)
                        items.append({
                            'description': line.description,
                            'qty': str(line.quantity),
                            'rate': str(line.rate),
                            'discount': str(line.discount_percent),
                            'line_amount': str(line.amount),
                        })
                    grand = sub - disc
                    summary = {
                        'sub_total': str(sub.quantize(Decimal('0.001'))),
                        'total_discount': str(disc.quantize(Decimal('0.001'))),
                        'grand_total': str(grand.quantize(Decimal('0.001'))),
                    }
                    date_iso = db_bill.bill_date.isoformat() if getattr(db_bill, 'bill_date', None) else ''
                    date_display = db_bill.bill_date.strftime('%d/%m/%Y') if getattr(db_bill, 'bill_date', None) else ''
                    bill_dict = {
                        'id': db_bill.id,
                        'number': db_bill.bill_number,
                        'vendor_name': db_bill.supplier.name if db_bill.supplier else '',
                        'vendor_id': db_bill.supplier.id if db_bill.supplier else '',
                        'date': date_iso,
                        'date_display': date_display,
                        'status': db_bill.status,
                        'items': items,
                    }
                    return render(request, 'bill_detail.html', {'bill': bill_dict, 'session_raw': session_raw, 'summary': summary})
                except Bill.DoesNotExist:
                    pass

            # if items exist in session, normalize keys and compute summary
            sub = Decimal('0')
            disc = Decimal('0')
            norm_items = []
            for it in items:
                try:
                    q = Decimal(str(it.get('qty') or it.get('quantity') or '0'))
                    r = Decimal(str(it.get('rate') or it.get('price') or '0'))
                    d = Decimal(str(it.get('discount') or it.get('discount_percent') or '0'))
                    line_total = q * r
                    line_net = q * r * (Decimal('1') - (d / Decimal('100')))
                    sub += line_total
                    disc += (line_total - line_net)
                    norm_items.append({
                        'description': it.get('description') or it.get('item') or '',
                        'qty': str(q),
                        'rate': str(r),
                        'discount': str(d),
                        'line_amount': str(line_net),
                    })
                except Exception:
                    continue
            grand = sub - disc
            summary = {
                'sub_total': str(sub.quantize(Decimal('0.001'))),
                'total_discount': str(disc.quantize(Decimal('0.001'))),
                'grand_total': str(grand.quantize(Decimal('0.001'))),
            }
            # normalize date from session if present
            s_date_raw = session_bill.get('date') or session_bill.get('bill_date') or ''
            date_iso = ''
            date_display = ''
            try:
                if s_date_raw:
                    # expect YYYY-MM-DD or similar
                    from datetime import datetime
                    dt = datetime.fromisoformat(s_date_raw)
                    date_iso = dt.date().isoformat()
                    date_display = dt.date().strftime('%d/%m/%Y')
            except Exception:
                # try alternative parsing
                try:
                    from datetime import datetime
                    dt = datetime.strptime(s_date_raw, '%Y-%m-%d')
                    date_iso = dt.date().isoformat()
                    date_display = dt.date().strftime('%d/%m/%Y')
                except Exception:
                    date_iso = s_date_raw
                    date_display = s_date_raw

            bill_dict = {
                'id': None,
                'number': session_bill.get('number', ''),
                'vendor_name': session_bill.get('vendor_name') or session_bill.get('supplier_name') or session_bill.get('supplier') or '',
                'date': date_iso,
                'date_display': date_display,
                'status': session_bill.get('status', ''),
                'items': norm_items,
            }
            return render(request, 'bill_detail.html', {'bill': bill_dict, 'session_raw': session_raw, 'summary': summary})

    # No bill found
    raise Http404('Bill not found')


def edit_bill(request, bill_id):
    """Render the add/edit bill form prefilled for the given `bill_id`.

    This replaces the temporary redirect and allows opening the bill for
    editing. The actual POST/update behavior is still handled by
    `add_bill` (which creates new bills); edits currently should submit to
    the same endpoint or be extended later. For now we prefill the form so
    users can modify and submit.
    """
    try:
        bill = Bill.objects.select_related('supplier').prefetch_related('lines').get(pk=int(bill_id))
    except Exception:
        raise Http404('Bill not found')

    # build suppliers sample (same as add_bill) for inline suggestions
    suppliers = Supplier.objects.all().order_by('-id')[:200]
    suppliers_sample = []
    for s in suppliers:
        suppliers_sample.append({'id': s.id, 'name': s.name, 'phone': getattr(s, 'phone', ''), 'locations': [], 'address': getattr(s, 'address', '')})

    # prepare bill data for client-side hydration into the editable add form
    items = []
    for line in bill.lines.all():
        items.append({
            'description': line.description,
            'qty': float(line.quantity) if line.quantity is not None else 0,
            'rate': float(line.rate) if line.rate is not None else 0,
            'discount': float(line.discount_percent) if line.discount_percent is not None else 0,
            'amount': float(line.amount) if line.amount is not None else 0,
            'account_type': getattr(line, 'account_type', 'inventory'),
        })

    bill_dict = {
        'id': bill.id,
        'number': getattr(bill, 'bill_number', ''),
        'bill_number': getattr(bill, 'bill_number', ''),
        'supplier_id': bill.supplier.id if bill.supplier else None,
        'supplier_name': bill.supplier.name if bill.supplier else '',
        'date': bill.bill_date.isoformat() if getattr(bill, 'bill_date', None) else '',
        'bill_date': bill.bill_date.isoformat() if getattr(bill, 'bill_date', None) else '',
        'notes': getattr(bill, 'notes', '') if hasattr(bill, 'notes') else '',
        'items': items,
    }

    import json as _json
    bill_json = _json.dumps(bill_dict)

    # suppliers sample for client-side inline suggestions
    # (already built above as `suppliers_sample`)
    next_bill_number = bill_dict.get('bill_number') or 'BIL-000001'

    return render(request, 'bills_add.html', {
        'suppliers_sample': suppliers_sample,
        'next_bill_number': next_bill_number,
        'bill_json': bill_json,
        'bill': bill_dict,
    })


@login_required
def migrate_session_bills_view(request):
    """Migrate session-stored recent bills into persistent DB for the current user session.

    This is a utility endpoint for interactive migration: it will attempt to migrate
    each session bill using `migrate_session_bill` and report results.
    """
    recent = request.session.get('recent_bills', []) or []
    migrated = []
    failed = []
    for sb in recent:
        bill, reason = migrate_session_bill(sb, dry_run=False)
        if bill:
            migrated.append({'number': getattr(bill, 'bill_number', ''), 'id': bill.id})
        else:
            failed.append(reason)

    # clear migrated session bills
    request.session['recent_bills'] = []
    request.session.modified = True

    return render(request, 'migrate_session_result.html', {'migrated': migrated, 'failed': failed})


@require_GET
def last_purchase_price(request):
    """Return last purchase price for a given supplier and part.

    Query params:
    - supplier_id (optional)
    - part_id (required)

    Response: {"price": "0.000"} or {"price": null}
    """
    supplier_id = request.GET.get('supplier_id')
    part_id = request.GET.get('part_id')
    from decimal import Decimal

    # Return stored purchase_price for the requested part when available
    try:
        if not part_id:
            return JsonResponse({'price': None})
        p = Part.objects.filter(pk=int(part_id)).first()
        if p and p.purchase_price is not None:
            return JsonResponse({'price': str(p.purchase_price)})
    except Exception:
        pass

    return JsonResponse({'price': None})


@csrf_exempt
def delete_vendor_payments(request):
    """Delete selected BillPayment records.

    Expects POST with JSON body: { selected: [id, id, ...] }
    For each deleted payment, revert supplier.amount when payment.status == 'paid',
    and update related bill.status if needed.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    try:
        import json
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
    except Exception:
        data = request.POST
    selected = data.get('selected') or []
    deleted = []
    skipped = []

    for sel in list(selected):
        try:
            pid = int(str(sel))
        except Exception:
            skipped.append(str(sel))
            continue
        try:
            bp = BillPayment.objects.select_related('supplier', 'bill').filter(pk=pid).first()
            if not bp:
                skipped.append(str(pid))
                continue

            with transaction.atomic():
                # revert supplier balance for paid payments
                try:
                    supplier = bp.supplier
                    if supplier and getattr(bp, 'status', '') == 'paid' and getattr(bp, 'amount', None) is not None:
                        supplier.amount = (supplier.amount or Decimal('0')) + Decimal(str(bp.amount or 0))
                        supplier.save()
                except Exception:
                    pass

                # update bill status if necessary
                try:
                    bill = bp.bill
                    if bill:
                        paid_amount = BillPayment.objects.filter(bill=bill, status='paid').exclude(pk=bp.pk).aggregate(total=Sum('amount'))['total'] or 0
                        try:
                            if Decimal(str(paid_amount or 0)) < Decimal(str(bill.grand_total or 0)) and bill.status == 'paid':
                                # mark as sent (closest existing non-paid state)
                                bill.status = 'sent'
                                bill.save()
                        except Exception:
                            pass
                except Exception:
                    pass

                bp.delete()
                deleted.append(str(pid))
        except Exception:
            skipped.append(str(sel))

    return JsonResponse({'deleted': deleted, 'skipped': skipped})


@login_required
def vendor_payment_detail(request, payment_id):
    """Render a simple detail page for a BillPayment record."""
    try:
        bp = BillPayment.objects.select_related('supplier', 'bill').get(pk=int(payment_id))
    except Exception:
        raise Http404('Payment not found')

    payment = {
        'id': bp.id,
        'amount': float(bp.amount or 0),
        'payment_date': bp.payment_date,
        'method': bp.get_method_display() if hasattr(bp, 'get_method_display') else bp.method,
        'status': bp.get_status_display() if hasattr(bp, 'get_status_display') else bp.status,
        'reference': bp.reference,
        'notes': bp.notes,
        'supplier_id': bp.supplier.id if bp.supplier else None,
        'supplier_name': bp.supplier.name if bp.supplier else '',
        'bill_id': bp.bill.id if bp.bill else None,
        'bill_number': bp.bill.bill_number if bp.bill else None,
    }

    return render(request, 'vendor_payment_detail.html', {'payment': payment})


@csrf_exempt
def delete_bills(request):
    """Delete selected bills. Accepts POST with JSON body {'selected': ['1','s-0', ...]}.

    Numeric values delete DB `Bill` rows. Values prefixed with 's-' remove session
    entries at that index from `request.session['recent_bills']`.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    try:
        import json
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
    except Exception:
        data = request.POST
    selected = data.get('selected') or []
    deleted = []
    skipped = []

    # handle DB deletions (revert supplier balances and part quantities)
    for sel in list(selected):
        try:
            s = str(sel)
            if s.startswith('s-'):
                # session entry: collect indices to remove later
                continue
            bid = int(s)
            b = Bill.objects.select_related('supplier').prefetch_related('lines').filter(pk=bid).first()
            if not b:
                skipped.append(s)
                continue
            # perform revert and delete inside a transaction
            try:
                with transaction.atomic():
                    # revert supplier amount
                    try:
                        supplier = b.supplier
                        if supplier and getattr(b, 'grand_total', None) is not None:
                            from decimal import Decimal
                            amt = Decimal(str(getattr(b, 'grand_total', '0') or '0'))
                            supplier.amount = (supplier.amount or Decimal('0')) - amt
                            supplier.save()
                    except Exception:
                        pass

                    # revert parts quantities based on bill lines (lock rows)
                    try:
                        for line in b.lines.all():
                            try:
                                part = Part.objects.select_for_update().filter(name__iexact=(line.description or '')).first()
                                if part:
                                    # subtract the purchased quantity, don't go below zero
                                    try:
                                        q = int(line.quantity or 0)
                                    except Exception:
                                        q = 0
                                    part.quantity = max(0, (part.quantity or 0) - q)
                                    part.save()
                            except Exception:
                                continue
                    except Exception:
                        pass

                    # finally delete the bill
                    b.delete()
                    deleted.append(s)
            except Exception:
                skipped.append(s)
        except Exception:
            skipped.append(str(sel))

    # handle session removals
    session_indices = [int(str(s)[2:]) for s in selected if isinstance(s, str) and s.startswith('s-')]
    if session_indices:
        recent = request.session.get('recent_bills', []) or []
        # remove by index (descending to keep indices valid)
        for idx in sorted(session_indices, reverse=True):
            if 0 <= idx < len(recent):
                recent.pop(idx)
                deleted.append(f's-{idx}')
            else:
                skipped.append(f's-{idx}')
        request.session['recent_bills'] = recent

    return JsonResponse({'deleted': deleted, 'skipped': skipped})
