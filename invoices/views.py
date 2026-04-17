
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Invoice
from django.core.paginator import Paginator
from django.db import models
from django import forms
from django.utils import timezone
from django.http import JsonResponse
from django.db.models.functions import TruncMonth
from django.db.models.functions import Substr, Cast
from django.db.models import IntegerField
import logging

# module logger for invoice hardening audit
logger = logging.getLogger(__name__)

@login_required
def add_expense_category_ajax(request):
    """AJAX endpoint to quickly create an ExpenseCategory from forms.
    Expects POST with 'name' (and optional 'description'). Returns JSON {success,id,name}.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    name = (request.POST.get('name') or '').strip()
    desc = (request.POST.get('description') or '').strip()
    if not name:
        return JsonResponse({'success': False, 'error': 'Name required'}, status=400)
    try:
        from .models import ExpenseCategory
        cat = ExpenseCategory.objects.create(name=name, description=desc or None)
        return JsonResponse({'success': True, 'id': cat.id, 'name': cat.name})
    except Exception as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=500)


@login_required
def edit_expense_category_ajax(request, cat_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    name = (request.POST.get('name') or '').strip()
    if not name:
        return JsonResponse({'success': False, 'error': 'Name required'}, status=400)
    try:
        from .models import ExpenseCategory
        cat = ExpenseCategory.objects.get(pk=cat_id)
        cat.name = name
        cat.save()
        return JsonResponse({'success': True, 'id': cat.id, 'name': cat.name})
    except ExpenseCategory.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Not found'}, status=404)
    except Exception as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=500)


@login_required
def delete_expense_category_ajax(request, cat_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    try:
        from .models import ExpenseCategory
        cat = ExpenseCategory.objects.get(pk=cat_id)
        # prevent deletion if used
        if cat.expenses.exists() or cat.recurrings.exists():
            return JsonResponse({'success': False, 'error': 'Category in use'}, status=400)
        cat.delete()
        return JsonResponse({'success': True})
    except ExpenseCategory.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Not found'}, status=404)
    except Exception as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=500)

# كشف حساب عميل (للطباعة)
@login_required
def account_statement_print_view(request):
    from clients.models import Client
    client = None
    invoices = []
    query = request.GET.get('q', '').strip()
    if query:
        clients = Client.objects.filter(
            models.Q(first_name__icontains=query) |
            models.Q(last_name__icontains=query) |
            models.Q(phone_number__icontains=query) |
            models.Q(customer_id__icontains=query) |
            models.Q(invoices__car__plate_number__icontains=query)
        ).distinct()
        if clients.exists():
            client = clients.first()
            invoices = client.invoices.select_related('car').order_by('-created_at')
    return render(request, 'account_statement_print.html', {
        'client': client,
        'invoices': invoices,
        'query': query,
    })

# كشف حساب عميل
@login_required
def account_statement_view(request):
    from clients.models import Client
    client = None
    invoices = []
    payments = []
    query = request.GET.get('q', '').strip()
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()
    if query:
        # البحث بالاسم أو رقم الهاتف أو رقم العميل أو رقم السيارة
        clients = Client.objects.filter(
            models.Q(first_name__icontains=query) |
            models.Q(last_name__icontains=query) |
            models.Q(phone_number__icontains=query) |
            models.Q(customer_id__icontains=query) |
            models.Q(invoices__car__plate_number__icontains=query)
        ).distinct()
        if clients.exists():
            client = clients.first()
            invoices = client.invoices.select_related('car').order_by('-created_at')
            # فلترة بالتواريخ
            if from_date:
                invoices = invoices.filter(created_at__gte=from_date)
            if to_date:
                invoices = invoices.filter(created_at__lte=to_date)
            payments = client.invoices.prefetch_related('payments')
    return render(request, 'account_statement.html', {
        'client': client,
        'invoices': invoices,
        'query': query,
        'from_date': from_date,
        'to_date': to_date,
    })

# طباعة فاتورة واحدة
@login_required
def print_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    return render(request, 'payment_success.html', {'invoice': invoice})

@login_required
def invoices_print_list(request):
    # Order by id descending so newest invoice numbers appear first (INV-00000...)
    invoices = Invoice.objects.select_related('client', 'car').order_by('-id')
    car_number = request.GET.get('car_number', '').strip()
    invoice_number = request.GET.get('invoice_number', '').strip()
    if car_number:
        invoices = invoices.filter(car__plate_number__icontains=car_number)
    if invoice_number:
        invoices = invoices.filter(invoice_number__icontains=invoice_number)
    return render(request, 'invoices_print_list.html', {'invoices': invoices})


@login_required
def financial_management(request):
    from django.db.models import Sum, Count, Q
    import datetime
    from django.utils import timezone
    # Read filters from request
    status = (request.GET.get('status') or '').strip().lower()
    q = (request.GET.get('q') or '').strip()
    from_date = (request.GET.get('from') or '').strip()
    to_date = (request.GET.get('to') or '').strip()
    # months selector for charts (6,12,24)
    try:
        months = int(request.GET.get('months') or 12)
    except Exception:
        months = 12
    if months not in (6, 12, 24):
        months = 12

    # Base queryset: annotate numeric part of invoice_number (strip 'INV-' prefix) and order by it desc
    # This ensures INV-000064 sorts before INV-000063 regardless of created_at ordering.
    qs = Invoice.objects.select_related('client', 'car').annotate(
        _inv_num=Cast(Substr('invoice_number', 5, 10), IntegerField())
    ).order_by('-_inv_num', '-created_at')

    # Apply status filter
    if status == 'paid':
        qs = qs.filter(paid=True)
    elif status == 'unpaid':
        qs = qs.filter(paid=False)
    elif status == 'overdue':
        # unpaid and older than 30 days
        thirty_days_ago = timezone.now() - datetime.timedelta(days=30)
        qs = qs.filter(paid=False, created_at__lte=thirty_days_ago)

    # Apply date filters if provided
    try:
        if from_date:
            qs = qs.filter(created_at__gte=from_date)
        if to_date:
            qs = qs.filter(created_at__lte=to_date)
    except Exception:
        pass

    # Search (client name, invoice number, car plate)
    if q:
        qs = qs.filter(
            Q(invoice_number__icontains=q) |
            Q(client__first_name__icontains=q) |
            Q(client__last_name__icontains=q) |
            Q(car__plate_number__icontains=q)
        ).distinct()

    # Aggregates based on current filter (but also provide global totals)
    total_revenue = Invoice.objects.aggregate(total=Sum('amount'))['total'] or 0
    collected = Invoice.objects.filter(paid=True).aggregate(total=Sum('amount'))['total'] or 0
    outstanding = Invoice.objects.filter(paid=False).aggregate(total=Sum('amount'))['total'] or 0

    # Overdue invoices: unpaid and older than 30 days (global)
    thirty_days_ago = timezone.now() - datetime.timedelta(days=30)
    overdue_count = Invoice.objects.filter(paid=False, created_at__lte=thirty_days_ago).count()

    # COGS and profit calculations
    try:
        from .models import InvoiceItem
        from decimal import Decimal
        # InvoiceItem does not have a direct FK to Part in this schema, so attempt
        # to resolve parts by matching item descriptions to Part (best-effort).
        try:
            from inventory.utils import find_part_for_description
            from bills.models import BillLine
            from inventory.models import Part
            cogs_total = Decimal('0')
            invoice_line_expenses = Decimal('0')
            unmatched_items = []
            items_qs = InvoiceItem.objects.filter(invoice__in=qs).values('description', 'quantity', 'rate', 'total', 'invoice__invoice_number', 'invoice')
            for it in items_qs:
                try:
                    desc = (it.get('description') or '').strip()
                    qty = Decimal(str(it.get('quantity') or 0))
                except Exception:
                    continue
                if not desc or qty == 0:
                    continue
                try:
                    part = find_part_for_description(desc)
                except Exception:
                    part = None

                # determine line total (fallback to rate*qty)
                line_total = None
                try:
                    if it.get('total') is not None:
                        line_total = Decimal(str(it.get('total')))
                    else:
                        line_total = qty * Decimal(str(it.get('rate') or 0))
                except Exception:
                    line_total = None

                # Decide whether this line is inventory (COGS) or expense
                line_is_inventory = None
                # Priority 1: BillLine.account_type if we can find a recent purchase line for the same part
                try:
                    if part:
                        last_purchase_line = BillLine.objects.filter(part=part).select_related('bill').order_by('-bill__bill_date', '-bill__created_at').first()
                        if last_purchase_line and getattr(last_purchase_line, 'account_type', None):
                            line_is_inventory = (last_purchase_line.account_type == 'inventory')
                except Exception:
                    line_is_inventory = None

                # Priority 2: use Part.is_inventory
                try:
                    if line_is_inventory is None and part:
                        line_is_inventory = bool(getattr(part, 'is_inventory', True))
                except Exception:
                    line_is_inventory = None

                # Now accumulate values
                try:
                    if line_is_inventory is True and part and getattr(part, 'purchase_price', None) is not None:
                        # inventory -> use part purchase_price if available
                        try:
                            cogs_total += (qty * Decimal(str(part.purchase_price)))
                        except Exception:
                            if line_total is not None:
                                cogs_total += line_total
                    elif line_is_inventory is False:
                        # explicitly marked expense
                        if line_total is not None:
                            invoice_line_expenses += line_total
                    else:
                        # fallback: if purchase_price available use it, otherwise use line total
                        if part and getattr(part, 'purchase_price', None) is not None:
                            try:
                                cogs_total += (qty * Decimal(str(part.purchase_price)))
                            except Exception:
                                if line_total is not None:
                                    cogs_total += line_total
                        else:
                            if line_total is not None:
                                cogs_total += line_total
                except Exception:
                    pass

                # record unmatched item metadata for visibility/debug
                try:
                    supplier_name = None
                    supplier_id = None
                    try:
                        candidate = None
                        if part is None:
                            candidate = Part.objects.filter(name__icontains=desc).first()
                        else:
                            candidate = part
                        if candidate:
                            last_line = BillLine.objects.select_related('bill__supplier').filter(part=candidate).order_by('-bill__bill_date', '-bill__created_at').first()
                            if last_line and last_line.bill and last_line.bill.supplier:
                                supplier = last_line.bill.supplier
                            else:
                                supplier = getattr(candidate, 'supplier', None)
                            if supplier:
                                supplier_name = getattr(supplier, 'name', None)
                                supplier_id = getattr(supplier, 'id', None)
                    except Exception:
                        supplier_name = None
                        supplier_id = None

                    unmatched_items.append({
                        'invoice_id': it.get('invoice'),
                        'invoice_number': it.get('invoice__invoice_number') or '',
                        'description': desc,
                        'quantity': float(qty),
                        'rate': float(it.get('rate') or 0),
                        'line_total': float(line_total) if line_total is not None else None,
                        'supplier_name': supplier_name,
                        'supplier_id': supplier_id,
                        'resolved_part_id': getattr(part, 'id', None) if part else None,
                    })
                except Exception:
                    pass

            cogs = cogs_total
        except Exception:
            cogs = 0
            invoice_line_expenses = Decimal('0')
    except Exception:
        cogs = 0
        invoice_line_expenses = Decimal('0')

    # Total expenses (suppliers/bills) — respect date filters if provided
    try:
        from bills.models import Bill
        bill_qs = Bill.objects.all()
        try:
            if from_date:
                bill_qs = bill_qs.filter(bill_date__gte=from_date)
            if to_date:
                bill_qs = bill_qs.filter(bill_date__lte=to_date)
        except Exception:
            pass
        try:
            total_expenses = bill_qs.aggregate(total=Sum('grand_total'))['total'] or 0
        except Exception:
            total_expenses = 0
        # include invoice-line-level expenses (lines marked as expense rather than inventory)
        try:
            from decimal import Decimal
            total_expenses = (total_expenses or 0) + (invoice_line_expenses if 'invoice_line_expenses' in locals() else Decimal('0'))
        except Exception:
            pass
        # include manual Expense records (app 'invoices'.Expense) in total_expenses
        try:
            from .models import Expense
            from django.db.models import Sum
            exp_qs = Expense.objects.all()
            try:
                if from_date:
                    exp_qs = exp_qs.filter(date__gte=from_date)
                if to_date:
                    exp_qs = exp_qs.filter(date__lte=to_date)
            except Exception:
                pass
            exp_sum = exp_qs.aggregate(total=Sum('amount'))['total'] or 0
            total_expenses = (total_expenses or 0) + exp_sum
        except Exception:
            pass
    except Exception:
        total_expenses = 0

    try:
        from decimal import Decimal
        # normalize values to Decimal for correct arithmetic (avoid accidental bool short-circuit)
        total_revenue_dec = Decimal(str(total_revenue or 0))
        cogs_dec = Decimal(str(cogs or 0))
        total_expenses_dec = Decimal(str(total_expenses or 0))

        # direct arithmetic without conditional short-circuits
        gross_profit = total_revenue_dec - cogs_dec
        net_profit = gross_profit - total_expenses_dec
    except Exception:
        # fallback: try numeric subtraction with available values but avoid forcing zeros blindly
        try:
            gross_profit = (total_revenue or 0) - (cogs if 'cogs' in locals() else 0)
            net_profit = gross_profit - (total_expenses if 'total_expenses' in locals() else 0)
        except Exception:
            gross_profit = 0
            net_profit = 0

    # Recent lists derived from filtered queryset
    recent_invoices = qs[:12]
    invoices_table = qs[:50]

    # Recent payments (latest 12) — order by numeric invoice number desc, then by payment_date
    try:
        from .models import Payment

        # annotate numeric part of related invoice's invoice_number and order by it
        recent_payments = (
            Payment.objects.select_related('invoice', 'invoice__client')
            .annotate(_inv_num=Cast(Substr('invoice__invoice_number', 5, 10), IntegerField()))
            .order_by('-_inv_num', '-payment_date')[:12]
        )
    except Exception:
        recent_payments = []

    # Suppliers / Bills: KPIs and recent lists (separate section)
    try:
        from bills.models import Bill, BillPayment
    except Exception:
        total_payables = 0
        paid_to_suppliers = 0
        outstanding_bills = 0
        overdue_bills_count = 0
        recent_bills = []
        recent_supplier_payments = []
    else:
        # totals (safe)
        try:
            total_payables = Bill.objects.aggregate(total=Sum('grand_total'))['total'] or 0
        except Exception:
            total_payables = 0
        try:
            paid_to_suppliers = BillPayment.objects.aggregate(total=Sum('amount'))['total'] or 0
        except Exception:
            paid_to_suppliers = 0
        outstanding_bills = (total_payables or 0) - (paid_to_suppliers or 0)

        # overdue bills: not paid and older than 30 days (using bill_date)
        try:
            thirty_days_ago_b = timezone.now() - datetime.timedelta(days=30)
            overdue_bills_count = Bill.objects.exclude(status='paid').filter(bill_date__lte=thirty_days_ago_b).count()
        except Exception:
            overdue_bills_count = 0

        # recent bills: try numeric bill_number ordering, fallback to bill_date
        try:
            recent_bills = (
                Bill.objects.select_related('supplier')
                .annotate(_bill_num=Cast(Substr('bill_number', 5, 10), IntegerField()))
                .order_by('-_bill_num', '-bill_date')[:12]
            )
        except Exception:
            recent_bills = Bill.objects.select_related('supplier').order_by('-bill_date')[:12]

        # recent supplier payments: try numeric bill ordering, fallback to payment_date
        try:
            recent_supplier_payments = (
                BillPayment.objects.select_related('bill', 'supplier')
                .annotate(_bill_num=Cast(Substr('bill__bill_number', 5, 10), IntegerField()))
                .order_by('-_bill_num', '-payment_date')[:12]
            )
        except Exception:
            recent_supplier_payments = BillPayment.objects.select_related('bill', 'supplier').order_by('-payment_date')[:12]

    return render(request, 'financial_management.html', {
        'total_revenue': total_revenue,
        'collected': collected,
        'outstanding': outstanding,
        'overdue_count': overdue_count,
        'recent_invoices': recent_invoices,
        'invoices_table': invoices_table,
        'recent_payments': recent_payments,
        'total_payables': total_payables,
        'paid_to_suppliers': paid_to_suppliers,
        'outstanding_bills': outstanding_bills,
        'overdue_bills_count': overdue_bills_count,
        'recent_bills': recent_bills,
        'recent_supplier_payments': recent_supplier_payments,
        'cogs_unmatched_items': unmatched_items if 'unmatched_items' in locals() else [],
        'cogs': cogs if 'cogs' in locals() else 0,
        'total_expenses': total_expenses if 'total_expenses' in locals() else 0,
        'gross_profit': gross_profit if 'gross_profit' in locals() else 0,
        'net_profit': net_profit if 'net_profit' in locals() else 0,
        'applied_status': status,
        'query': q,
        'from_date': from_date,
        'to_date': to_date,
        'months': months,
    })



@login_required
def expenses_list(request):
    from .models import Expense
    from django.db.models import Sum

    fd = request.GET.get('from')
    td = request.GET.get('to')
    qs = Expense.objects.select_related('category').order_by('-date')
    try:
        if fd:
            qs = qs.filter(date__gte=fd)
        if td:
            qs = qs.filter(date__lte=td)
    except Exception:
        pass

    total = qs.aggregate(total=Sum('amount'))['total'] or 0

    # build rows with recipient for display
    rows = []
    for e in qs[:200]:
        recipient = ''
        try:
            if e.note and 'To:' in e.note:
                recipient = e.note.split('To:')[-1].strip()
            else:
                recipient = e.payee or ''
        except Exception:
            recipient = e.payee or ''
        rows.append({'expense': e, 'recipient': recipient})

    return render(request, 'expenses_list.html', {'rows': rows, 'total': total, 'from_date': fd, 'to_date': td})


@login_required
def add_expense(request):
    from .forms import ExpenseForm
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        # Do not include the 'bill' field on the Add page
        if 'bill' in form.fields:
            form.fields.pop('bill')
        if form.is_valid():
            exp = form.save(commit=False)
            try:
                exp.created_by = request.user
            except Exception:
                pass
            # if a separate payee_recipient was provided, append to note for display
            try:
                recipient = (request.POST.get('payee_recipient') or '').strip()
                if recipient:
                    base_note = (exp.note or '').strip()
                    if base_note:
                        exp.note = base_note + '\nTo: ' + recipient
                    else:
                        exp.note = 'To: ' + recipient
            except Exception:
                pass
            # fallback: ensure exp.payee set from payee_recipient if payee input was empty
            try:
                if not (exp.payee and str(exp.payee).strip()):
                    rec = (request.POST.get('payee_recipient') or '').strip()
                    if rec:
                        exp.payee = rec
            except Exception:
                pass
            exp.save()
            return redirect('expenses_list')
    else:
        form = ExpenseForm()
        # Hide the bill selector on creation page — not needed for add
        if 'bill' in form.fields:
            form.fields.pop('bill')
    # provide user list for Payee dynamic dropdown (used when Payee = 'salary')
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        users_qs = User.objects.all().values('id', 'first_name', 'last_name', 'username')
        payee_users = []
        for u in users_qs:
            name = (u.get('first_name') or '').strip() or (u.get('username') or '')
            if u.get('last_name'):
                ln = (u.get('last_name') or '').strip()
                if ln:
                    name = (name + ' ' + ln).strip()
            payee_users.append({'id': u['id'], 'name': name})
    except Exception:
        payee_users = []

    return render(request, 'expenses_add.html', {'form': form, 'payee_users': payee_users})


@login_required
def edit_expense(request, expense_id):
    from .forms import ExpenseForm
    from .models import Expense
    exp = get_object_or_404(Expense, id=expense_id)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=exp)
        # Hide the bill selector on edit page — not needed
        if 'bill' in form.fields:
            form.fields.pop('bill')
        if form.is_valid():
            obj = form.save(commit=False)
            # ensure payee is preserved: prefer posted hidden payee_recipient, else parse posted note, else keep existing
            try:
                posted_note = (request.POST.get('note') or '').strip()
                posted_rec = (request.POST.get('payee_recipient') or '').strip()
                parsed_rec = ''
                if posted_note and 'To:' in posted_note and not posted_rec:
                    parsed_rec = posted_note.split('To:')[-1].strip()
                use_rec = posted_rec or parsed_rec or (obj.payee or '')
                if use_rec:
                    obj.payee = use_rec
            except Exception:
                pass
            # fallback: ensure obj.payee populated from payee_recipient if missing
            try:
                if not (obj.payee and str(obj.payee).strip()):
                    rec = (request.POST.get('payee_recipient') or '').strip()
                    if rec:
                        obj.payee = rec
            except Exception:
                pass
            try:
                # handle payee_recipient on edit as well
                try:
                    recipient = (request.POST.get('payee_recipient') or '').strip()
                    posted_note = (request.POST.get('note') or '').strip()
                    # If user edited the note (posted_note non-empty and not just a To: line), keep it.
                    import re
                    if posted_note:
                        # if posted_note is only a To: line (or contains To: as last part), and we have a recipient, normalize it
                        if recipient and re.match(r'^\s*To:\s*', posted_note):
                            parts = re.split(r'\nTo:\s*', posted_note, maxsplit=1)
                            base = parts[0].strip() if len(parts) == 2 else ''
                            if base:
                                obj.note = base + '\nTo: ' + recipient
                            else:
                                obj.note = 'To: ' + recipient
                        else:
                            # user provided a custom note — preserve it
                            obj.note = posted_note
                    else:
                        # no posted note; if recipient provided, update or add To: part based on existing note
                        if recipient:
                            base_note = (obj.note or '').strip()
                            if base_note and 'To:' in base_note:
                                parts = base_note.split('To:')
                                base = parts[0].strip()
                                obj.note = (base + '\nTo: ' + recipient).strip()
                            elif base_note:
                                obj.note = base_note + '\nTo: ' + recipient
                            else:
                                obj.note = 'To: ' + recipient
                except Exception:
                    pass
                obj.save()
            except Exception:
                pass
            return redirect('expenses_list')
    else:
        form = ExpenseForm(instance=exp)
        # Hide the bill selector on edit page — not needed
        if 'bill' in form.fields:
            form.fields.pop('bill')
    # include payee users for edit page as well
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        users_qs = User.objects.all().values('id', 'first_name', 'last_name', 'username')
        payee_users = []
        for u in users_qs:
            name = (u.get('first_name') or '').strip() or (u.get('username') or '')
            if u.get('last_name'):
                ln = (u.get('last_name') or '').strip()
                if ln:
                    name = (name + ' ' + ln).strip()
            payee_users.append({'id': u['id'], 'name': name})
    except Exception:
        payee_users = []

    # derive existing_recipient from note for template prefill
    try:
        existing_recipient = ''
        if exp.note and 'To:' in exp.note:
            existing_recipient = exp.note.split('To:')[-1].strip()
        else:
            existing_recipient = exp.payee or ''
    except Exception:
        existing_recipient = exp.payee or ''

    return render(request, 'expenses_add.html', {'form': form, 'editing': True, 'expense': exp, 'payee_users': payee_users, 'existing_recipient': existing_recipient})


@login_required
def delete_expense(request, expense_id):
    from .models import Expense
    from django.contrib import messages
    exp = get_object_or_404(Expense, id=expense_id)
    if request.method == 'POST':
        try:
            exp.delete()
            messages.success(request, 'Expense deleted.')
        except Exception:
            messages.error(request, 'Could not delete expense.')
        return redirect('expenses_list')
    return render(request, 'expenses_delete.html', {'expense': exp})


@login_required
def complete_expense(request, expense_id):
    from .models import Expense
    from .forms import CompleteExpenseForm
    from django.contrib import messages
    exp = get_object_or_404(Expense, id=expense_id)
    if request.method == 'POST':
        form = CompleteExpenseForm(request.POST, instance=exp)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.status = 'posted'
            try:
                obj.save()
                messages.success(request, 'Expense completed and posted.')
            except Exception:
                messages.error(request, 'Could not complete expense.')
            return redirect('expenses_list')
    else:
        form = CompleteExpenseForm(instance=exp)
    return render(request, 'expenses_complete.html', {'form': form, 'expense': exp})


@login_required
def recurring_list(request):
    from .models import RecurringExpense
    qs = RecurringExpense.objects.select_related('category').order_by('-start_date')
    return render(request, 'recurring_list.html', {'recurrings': qs})


@login_required
def add_recurring(request):
    from .forms import RecurringExpenseForm
    if request.method == 'POST':
        form = RecurringExpenseForm(request.POST)
        if form.is_valid():
            rec = form.save(commit=False)
            try:
                rec.created_by = request.user
            except Exception:
                pass
            rec.save()
            return redirect('recurring_list')
    else:
        # prefill next_date and start_date with today
        from django.utils import timezone
        today = timezone.now().date()
        form = RecurringExpenseForm(initial={'start_date': today, 'next_date': today})
    # provide user list for Payee dynamic dropdown (used when Payee = 'salary')
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        users_qs = User.objects.all().values('id', 'first_name', 'last_name', 'username')
        payee_users = []
        for u in users_qs:
            name = (u.get('first_name') or '').strip() or (u.get('username') or '')
            if u.get('last_name'):
                ln = (u.get('last_name') or '').strip()
                if ln:
                    name = (name + ' ' + ln).strip()
            payee_users.append({'id': u['id'], 'name': name})
    except Exception:
        payee_users = []

    # remove payee fields from the form rendering so they don't appear as separate rows
    # we'll render hidden inputs in the template and let JS update them
    try:
        for f in ('payee', 'payee_recipient', 'payee_month'):
            if f in form.fields:
                form.fields.pop(f)
    except Exception:
        pass

    return render(request, 'recurring_add.html', {'form': form, 'payee_users': payee_users})


@login_required
def run_recurring_once(request):
    # staff-only utility endpoint to run due recurrences immediately (for testing)
    if not getattr(request.user, 'is_staff', False):
        return redirect('invoices_list')
    from .models import RecurringExpense, Expense
    import datetime
    from django.utils import timezone
    today = timezone.now().date()
    created = 0
    def advance_date(d, freq, interval=1):
        # simple advancer without external deps
        if freq == 'daily':
            return d + datetime.timedelta(days=interval)
        if freq == 'weekly':
            return d + datetime.timedelta(weeks=interval)
        if freq == 'monthly':
            # roll months
            month = d.month - 1 + interval
            year = d.year + month // 12
            month = month % 12 + 1
            day = min(d.day, 28)
            return datetime.date(year, month, day)
        if freq == 'yearly':
            try:
                return d.replace(year=d.year + interval)
            except Exception:
                return d
        return d

    qs = RecurringExpense.objects.filter(active=True).filter(next_date__lte=today)
    for r in qs:
        # ensure not past end_date
        if r.end_date and r.next_date > r.end_date:
            continue
        try:
            if getattr(r, 'reminder_only', False):
                Expense.objects.create(date=r.next_date, amount=None, category=r.category, note=(r.note or '') + ' (Reminder)', created_by=request.user, status='draft')
            else:
                Expense.objects.create(date=r.next_date, amount=r.amount, category=r.category, note=r.note, created_by=request.user)
            created += 1
        except Exception:
            continue
        # update next_date and last_run
        try:
            next_d = advance_date(r.next_date, r.frequency, r.interval)
            r.next_date = next_d
            from django.utils import timezone as _tz
            r.last_run = _tz.now()
            r.save()
        except Exception:
            pass

    return render(request, 'recurring_run_result.html', {'created': created})


@login_required
def edit_recurring(request, recurring_id):
    from .models import RecurringExpense
    from .forms import RecurringExpenseForm
    rec = get_object_or_404(RecurringExpense, id=recurring_id)
    if request.method == 'POST':
        form = RecurringExpenseForm(request.POST, instance=rec)
        if form.is_valid():
            obj = form.save(commit=False)
            try:
                obj.save()
            except Exception:
                pass
            return redirect('recurring_list')
    else:
        form = RecurringExpenseForm(instance=rec)
    # provide user list for Payee dynamic dropdown (used when Payee = 'salary')
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        users_qs = User.objects.all().values('id', 'first_name', 'last_name', 'username')
        payee_users = []
        for u in users_qs:
            name = (u.get('first_name') or '').strip() or (u.get('username') or '')
            if u.get('last_name'):
                ln = (u.get('last_name') or '').strip()
                if ln:
                    name = (name + ' ' + ln).strip()
            payee_users.append({'id': u['id'], 'name': name})
    except Exception:
        payee_users = []

    # remove payee fields from the form rendering so they don't appear as separate rows
    try:
        for f in ('payee', 'payee_recipient', 'payee_month'):
            if f in form.fields:
                form.fields.pop(f)
    except Exception:
        pass

    return render(request, 'recurring_add.html', {'form': form, 'editing': True, 'recurring': rec, 'payee_users': payee_users})


@login_required
def delete_recurring(request, recurring_id):
    from .models import RecurringExpense
    from django.contrib import messages
    rec = get_object_or_404(RecurringExpense, id=recurring_id)
    if request.method == 'POST':
        try:
            rec.delete()
            messages.success(request, 'Recurring expense deleted.')
        except Exception:
            messages.error(request, 'Could not delete recurring expense.')
        return redirect('recurring_list')
    return render(request, 'recurring_delete.html', {'recurring': rec})


@login_required
def create_recurring_now(request, recurring_id):
    # create an Expense now from a RecurringExpense (manual action)
    from .models import RecurringExpense
    from django.contrib import messages
    rec = get_object_or_404(RecurringExpense, id=recurring_id)
    if request.method == 'POST':
        try:
            e = rec.create_expense(user=request.user)
            messages.success(request, f'Expense created (id={e.id}).')
        except Exception as exc:
            messages.error(request, f'Could not create expense: {exc}')
        return redirect('recurring_list')
    # If GET, just redirect back (or could show a confirmation)
    return redirect('recurring_list')


@login_required
def charts_data(request):
    from django.db.models import Sum, Case, When, FloatField
    import datetime
    # build last 12 months labels (including current)
    now = timezone.now()
    start_month = now.replace(day=1)

    months = []
    for i in range(11, -1, -1):
        y = start_month.year
        m = start_month.month - i
        while m <= 0:
            m += 12
            y -= 1
        months.append((y, m))

    labels = []
    totals = []
    paid_data = []
    unpaid_data = []

    for (y, m) in months:
        labels.append(datetime.date(y, m, 1).strftime('%b %Y'))
        month_qs = Invoice.objects.filter(created_at__year=y, created_at__month=m)
        total_val = month_qs.aggregate(total=Sum('amount'))['total'] or 0
        paid_val = month_qs.filter(paid=True).aggregate(total=Sum('amount'))['total'] or 0
        unpaid_val = month_qs.filter(paid=False).aggregate(total=Sum('amount'))['total'] or 0
        totals.append(float(total_val or 0))
        paid_data.append(float(paid_val or 0))
        unpaid_data.append(float(unpaid_val or 0))

    return JsonResponse({'labels': labels, 'total': totals, 'paid': paid_data, 'unpaid': unpaid_data})


@login_required
def reports_view(request):
    """Render the Reports page (MVP)."""
    from django.utils import timezone
    # read filters
    status = (request.GET.get('status') or '').strip().lower()
    from_date = (request.GET.get('from') or '').strip()
    to_date = (request.GET.get('to') or '').strip()

    # basic KPIs (respecting filters would be implemented in JSON endpoints)
    from django.db.models import Sum
    total_revenue = Invoice.objects.aggregate(total=Sum('amount'))['total'] or 0
    collected = Invoice.objects.filter(paid=True).aggregate(total=Sum('amount'))['total'] or 0
    outstanding = Invoice.objects.filter(paid=False).aggregate(total=Sum('amount'))['total'] or 0

    from django.utils import timezone
    import datetime
    thirty_days_ago = timezone.now() - datetime.timedelta(days=30)
    overdue_count = Invoice.objects.filter(paid=False, created_at__lte=thirty_days_ago).count()

    return render(request, 'invoices/reports.html', {
        'total_revenue': total_revenue,
        'collected': collected,
        'outstanding': outstanding,
        'overdue_count': overdue_count,
        'applied_status': status,
        'from_date': from_date,
        'to_date': to_date,
    })


@login_required
def reports_revenue_json(request):
    """Return revenue summary (monthly) as JSON for charts and table.

    Query params: from, to, status
    """
    from django.db.models import Sum
    import datetime
    from django.utils import timezone

    # parse date filters
    fd = request.GET.get('from')
    td = request.GET.get('to')
    status = (request.GET.get('status') or '').strip().lower()

    qs = Invoice.objects.all()
    if fd:
        try:
            qs = qs.filter(created_at__date__gte=fd)
        except Exception:
            pass
    if td:
        try:
            qs = qs.filter(created_at__date__lte=td)
        except Exception:
            pass
    if status == 'paid':
        qs = qs.filter(paid=True)
    elif status == 'unpaid':
        qs = qs.filter(paid=False)
    elif status == 'overdue':
        thirty = timezone.now() - datetime.timedelta(days=30)
        qs = qs.filter(paid=False, created_at__lte=thirty)

    # group by month between from/to or last 12 months
    labels = []
    totals = []

    # determine range
    try:
        if fd and td:
            start = datetime.datetime.strptime(fd, '%Y-%m-%d').date().replace(day=1)
            end = datetime.datetime.strptime(td, '%Y-%m-%d').date().replace(day=1)
        else:
            now = timezone.now().date()
            end = now.replace(day=1)
            # last 11 months + current = 12
            start = (end - datetime.timedelta(days=365)).replace(day=1)
    except Exception:
        now = timezone.now().date()
        end = now.replace(day=1)
        start = (end - datetime.timedelta(days=365)).replace(day=1)

    cur = start
    while cur <= end:
        labels.append(cur.strftime('%b %Y'))
        # calculate month range
        next_month = (cur.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
        month_sum = qs.filter(created_at__date__gte=cur, created_at__date__lt=next_month).aggregate(total=Sum('amount'))['total'] or 0
        totals.append(float(month_sum))
        cur = next_month

    return JsonResponse({'labels': labels, 'total': totals})


@login_required
def reports_revenue_csv(request):
    """Export revenue summary (per month) as CSV."""
    import csv
    from django.http import HttpResponse
    resp = reports_revenue_json(request)
    data = resp.json() if hasattr(resp, 'json') else resp.content
    # resp is JsonResponse; convert to python
    if isinstance(resp, JsonResponse):
        data = resp.content
        import json as _json
        parsed = _json.loads(data)
    else:
        parsed = {}
    labels = parsed.get('labels', [])
    totals = parsed.get('total', [])

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="revenue_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Month', 'Total'])
    for l, t in zip(labels, totals):
        writer.writerow([l, t])
    return response


@login_required
def reports_aging_json(request):
    """Return aging buckets for unpaid invoices.

    Buckets: 0-30,31-60,61-90,90+
    """
    from django.utils import timezone
    import datetime
    from django.db.models import Sum

    now = timezone.now().date()
    buckets = [
        {'key': '0-30', 'min': 0, 'max': 30, 'count': 0, 'amount': 0},
        {'key': '31-60', 'min': 31, 'max': 60, 'count': 0, 'amount': 0},
        {'key': '61-90', 'min': 61, 'max': 90, 'count': 0, 'amount': 0},
        {'key': '90+', 'min': 91, 'max': 10000, 'count': 0, 'amount': 0},
    ]

    qs = Invoice.objects.filter(paid=False)
    # optional date/status filters
    fd = request.GET.get('from')
    td = request.GET.get('to')
    if fd:
        try:
            qs = qs.filter(created_at__date__gte=fd)
        except Exception:
            pass
    if td:
        try:
            qs = qs.filter(created_at__date__lte=td)
        except Exception:
            pass

    results = []
    # iterate invoices and classify
    for inv in qs.values('id', 'invoice_number', 'client__first_name', 'client__last_name', 'amount', 'created_at'):
        try:
            created = inv.get('created_at').date()
        except Exception:
            created = inv.get('created_at')
        age = (now - created).days if created else 0
        for b in buckets:
            if b['min'] <= age <= b['max']:
                b['count'] += 1
                b['amount'] += float(inv.get('amount') or 0)
                break
        results.append(inv)

    return JsonResponse({'buckets': buckets, 'invoices': results})


@login_required
def reports_aging_csv(request):
    import csv
    from django.http import HttpResponse
    resp = reports_aging_json(request)
    if isinstance(resp, JsonResponse):
        import json as _json
        parsed = _json.loads(resp.content)
    else:
        parsed = {}
    buckets = parsed.get('buckets', [])
    invoices = parsed.get('invoices', [])

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="aging_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Bucket', 'Count', 'Amount'])
    for b in buckets:
        writer.writerow([b.get('key'), b.get('count'), b.get('amount')])
    writer.writerow([])
    writer.writerow(['Invoice #', 'Client', 'Amount', 'Created At'])
    for inv in invoices:
        client = f"{inv.get('client__first_name','')} {inv.get('client__last_name','') or ''}".strip()
        writer.writerow([inv.get('invoice_number'), client, inv.get('amount'), inv.get('created_at')])
    return response


# Add invoice page (reuse maintenance-style invoice editor)
@login_required
def add_invoice(request):
    # minimal form to provide `maintenance_date` widget used by the template
    class _MiniForm(forms.Form):
        maintenance_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)

    # Prefill maintenance_date with today's date (editable by user)
    try:
        from django.utils import timezone
        today = timezone.now().date()
        form = _MiniForm(initial={'maintenance_date': today.strftime('%Y-%m-%d')})
    except Exception:
        form = _MiniForm()
    # clients sample for autocomplete (serialize to simple dicts so template JS can consume it)
    clients_sample = []
    try:
        from clients.models import Client
        for c in Client.objects.all()[:200]:
            try:
                plates = [car.plate_number for car in c.cars.all()[:5] if car.plate_number]
            except Exception:
                plates = []
            try:
                cars_list = [{'id': car.id, 'plate': car.plate_number} for car in c.cars.all()[:20] if car.plate_number]
            except Exception:
                cars_list = []
            clients_sample.append({
                'id': c.id,
                'name': f"{c.first_name} {c.last_name or ''}".strip(),
                'phone': getattr(c, 'phone', ''),
                'plates': plates,
                'cars': cars_list,
            })
    except Exception:
        clients_sample = []

    # compute next invoice number for prefilling
    next_invoice_number = ''
    last_invoice_number = ''
    try:
        last_invoice = Invoice.objects.order_by('-id').first()
        if last_invoice:
            try:
                last_invoice_number = last_invoice.invoice_number or ''
            except Exception:
                last_invoice_number = ''
            if last_invoice.invoice_number and last_invoice.invoice_number.upper().startswith('INV-'):
                try:
                    last_num = int(last_invoice.invoice_number.split('INV-')[-1])
                    next_invoice_number = f"INV-{(last_num+1):06d}"
                except Exception:
                    next_invoice_number = ''
            else:
                try:
                    v = int((last_invoice.invoice_number or '').strip())
                    next_invoice_number = f"INV-{(v+1):06d}"
                except Exception:
                    next_invoice_number = ''
    except Exception:
        next_invoice_number = ''
    if not next_invoice_number:
        next_invoice_number = 'INV-000001'

    # support create on POST for stock invoices
    if request.method == 'POST':
        # create a stock invoice: no car, items_json expected
        import json
        from decimal import Decimal
        from django.db import transaction
        from django.http import HttpResponseBadRequest
        items_json = request.POST.get('items_json')
        # simple subject field (single-line) saved on Invoice
        subject = request.POST.get('subject')
        selected_client_id = request.POST.get('selected_client_id')
        if not selected_client_id:
            return HttpResponseBadRequest('يرجى اختيار عميل')
        try:
            from clients.models import Client
            client_obj = Client.objects.get(id=int(selected_client_id))
        except Exception:
            return HttpResponseBadRequest('عميل غير موجود')

        try:
            items = json.loads(items_json) if items_json else []
        except Exception:
            items = []

        # early availability check
        try:
            from inventory.utils import check_items_availability, apply_inventory_changes_for_invoice
            shortages = check_items_availability(items, None)
            if shortages:
                first = shortages[0]
                pname = getattr(first[0], 'name', '') if first and first[0] else ''
                msg = f'الكمية غير متوفرة: {pname}. المتوفر: {first[1]} المطلوب: {first[2]}'
                return HttpResponseBadRequest(msg)
        except Exception:
            return HttpResponseBadRequest('فشل التحقق من المخزون')

        # create invoice and items transactionally
        try:
            from django.db import IntegrityError
            import time, re
            # Attempt creation with retry on UNIQUE constraint collisions
            attempt = 0
            use_invoice_number = next_invoice_number or 'INV-000001'
            invoice = None
            while True:
                try:
                    with transaction.atomic():
                        invoice = Invoice.objects.create(
                            invoice_number=use_invoice_number,
                            client=client_obj,
                            car=None,
                            amount=0,
                            paid=False,
                            created_at=timezone.now(),
                            type='stock',
                            subject=(subject or '')
                        )
                    break
                except IntegrityError:
                    attempt += 1
                    if attempt > 10:
                        # fallback to timestamp-suffixed unique value
                        use_invoice_number = f"{use_invoice_number}-{int(time.time())}-{attempt}"
                    else:
                        # try to increment numeric tail if in INV-000001 format
                        if use_invoice_number and use_invoice_number.upper().startswith('INV-'):
                            try:
                                tail = int(use_invoice_number.split('INV-')[-1])
                                tail += 1
                                use_invoice_number = f"INV-{tail:06d}"
                            except Exception:
                                use_invoice_number = use_invoice_number + f"-{attempt}"
                        else:
                            m = re.search(r"(\d+)$", use_invoice_number or '')
                            if m:
                                try:
                                    num = int(m.group(1)) + 1
                                    use_invoice_number = use_invoice_number[:m.start(1)] + str(num)
                                except Exception:
                                    use_invoice_number = use_invoice_number + f"-{attempt}"
                            else:
                                use_invoice_number = use_invoice_number + f"-{attempt}"

            if not invoice:
                raise Exception('Failed to create invoice after retries')

            total_amount = Decimal('0')
            from .models import InvoiceItem
            for it in items:
                desc = (it.get('description') or '').strip()
                try:
                    qty = Decimal(str(it.get('qty') or 0))
                except Exception:
                    qty = Decimal('0')
                try:
                    rate = Decimal(str(it.get('rate') or 0))
                except Exception:
                    rate = Decimal('0')
                try:
                    discount = Decimal(str(it.get('discount') or 0))
                except Exception:
                    discount = Decimal('0')
                line_total = (qty * rate * (Decimal('1') - (discount / Decimal('100')))).quantize(Decimal('0.001'))
                if not desc and qty == 0 and rate == 0:
                    continue
                # Ignore service entries on stock invoice (frontend may send them)
                service_id = it.get('service_id') if isinstance(it, dict) else None
                part_id = it.get('part_id') if isinstance(it, dict) else None
                if service_id:
                    # safe-ignore services in stock sale
                    continue

                # try to resolve part if provided
                part = None
                try:
                    if part_id:
                        from inventory.models import Part as InventoryPart
                        part = InventoryPart.objects.filter(id=part_id).first()
                except Exception:
                    part = None

                # Only create invoice item for parts (stock sale)
                # Require `part_id` resolution from the frontend; do not fallback to name
                if not part:
                    # Enforce: reject any stock invoice that includes an item
                    # without a resolved `part_id`. This prevents ambiguous
                    # legacy name-only rows from being accepted in new data.
                    try:
                        logger.warning(
                            f"Invoice rejected: missing part_id | user={getattr(request, 'user', None)} | data={request.POST.dict() if hasattr(request.POST, 'dict') else str(request.POST)}"
                        )
                    except Exception:
                        pass
                    return HttpResponseBadRequest('Part selection required for all items in stock invoice')

                InvoiceItem.objects.create(
                    invoice=invoice,
                    part=part,
                    item_type='part',
                    description=desc,
                    quantity=qty,
                    rate=rate,
                    discount=discount,
                    total=line_total
                )
                total_amount += line_total

                # inventory adjustments are applied in batch below via
                # `apply_inventory_changes_for_invoice(items, decrement=True)`
                # to avoid double-decrement and keep rounding consistent.

            # apply inventory decrement for stock sale
            apply_inventory_changes_for_invoice(items, decrement=True)
            invoice.amount = float(total_amount)
            invoice.save()
        except Exception as e:
            return HttpResponseBadRequest('فشل في إنشاء الفاتورة: ' + str(e))
        from django.shortcuts import redirect
        # If the form was submitted with the "save_send" action, redirect
        # to the invoice print view so the user can print immediately.
        try:
            action = (request.POST.get('action') or '').strip()
            if action == 'save_send' and invoice and getattr(invoice, 'id', None):
                return redirect(f'/invoices/print/{invoice.id}/')
        except Exception:
            pass
        return redirect('invoices_list')

    return render(request, 'add_maintenance_record.html', {'form': form, 'car_instance': None, 'clients_sample': clients_sample, 'next_invoice_number': next_invoice_number, 'invoice_type': 'stock'})
from django.db import models
from cars.maintenance_models import MaintenanceRecord
from .forms import EditInvoiceForm
# عرض وتعديل جماعي لسجلات الصيانة المرتبطة بفاتورة
@login_required
def edit_invoice_records(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    records = MaintenanceRecord.objects.filter(invoice=invoice).select_related('service')
    return render(request, 'edit_invoice_records.html', {'invoice': invoice, 'records': records})
# تعديل الفاتورة (المبلغ فقط حالياً)
@login_required
def edit_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    # compute payment summaries for use both in GET and POST
    try:
        paid_amount = invoice.payments.filter(status='paid').aggregate(total=models.Sum('amount'))['total'] or 0
        paid_amount = float(paid_amount)
    except Exception:
        paid_amount = 0.0
    try:
        invoice_amount = float(invoice.amount or 0)
    except Exception:
        invoice_amount = 0.0
    remaining_balance = max(0.0, invoice_amount - paid_amount)
    amount_refunded = 0.0
    amount_in_excess = max(0.0, paid_amount - invoice_amount)

    if request.method == 'POST':
        # Accept fields from advanced edit form: items_json, discount, amount and created_at
        import json
        from decimal import Decimal, InvalidOperation
        amt = request.POST.get('amount')
        created = request.POST.get('created_at')
        items_json = request.POST.get('items_json')
        discount_post = request.POST.get('discount')
        updated = False

        # Parse items_json and compute totals if provided
        computed_total = None
        try:
            if items_json:
                data = json.loads(items_json)
                subtotal_before = Decimal('0')
                total_discount = Decimal('0')
                for it in data:
                    q = Decimal(str(it.get('qty', 0) or 0))
                    r = Decimal(str(it.get('rate', 0) or 0))
                    d = Decimal(str(it.get('disc', 0) or 0))
                    line_before = q * r
                    line_disc = (line_before * d) / Decimal('100')
                    subtotal_before += line_before
                    total_discount += line_disc
                computed_total = (subtotal_before - total_discount)
        except Exception:
            computed_total = None

        # If discount was provided separately, prefer computed discount if available
        try:
            disc_val = Decimal(str(discount_post)) if discount_post not in (None, '') else None
        except (InvalidOperation, TypeError):
            disc_val = None
        if computed_total is None and amt is not None and amt.strip() != '':
            try:
                computed_total = Decimal(str(amt))
            except Exception:
                computed_total = None

        if computed_total is not None:
            try:
                # persist invoice items to DB and set invoice.amount
                if items_json:
                    try:
                        from .models import InvoiceItem
                        from services.models import Service as ServiceModel
                        # EARLY AVAILABILITY CHECK: normalize items and abort with 400 on shortage
                        try:
                            from django.http import HttpResponseBadRequest
                            from inventory.utils import find_part_for_description, check_items_availability
                            from inventory.models import Part
                            # build normalized list similar to downstream logic
                            early_norm = []
                            for it in data:
                                desc = (it.get('description') or '').strip()
                                pid = it.get('part_id') or it.get('part') or None
                                if pid:
                                    try:
                                        p = Part.objects.filter(id=int(pid)).first()
                                        if p:
                                            desc = p.name
                                    except Exception:
                                        pass
                                if not desc:
                                    continue
                                try:
                                    q = Decimal(str(it.get('qty', 0) or 0))
                                except Exception:
                                    q = Decimal('0')
                                early_norm.append({'description': desc, 'qty': q})
                            # build existing map
                            early_existing = {}
                            try:
                                for ex in InvoiceItem.objects.filter(invoice=invoice):
                                    k = (ex.description or '').strip().lower()
                                    try:
                                        early_existing[k] = early_existing.get(k, Decimal('0')) + Decimal(str(ex.quantity or 0))
                                    except Exception:
                                        early_existing[k] = early_existing.get(k, Decimal('0'))
                            except Exception:
                                early_existing = {}
                            shortages = check_items_availability(early_norm, early_existing)
                            if shortages:
                                first = shortages[0]
                                pname = getattr(first[0], 'name', '') if first and first[0] else ''
                                msg = f'الكمية غير متوفرة: {pname}. المتوفر: {first[1]} المطلوب: {first[2]}'
                                return HttpResponseBadRequest(msg)
                        except Exception:
                            # if early check fails unexpectedly, be conservative and abort
                            from django.http import HttpResponseBadRequest
                            return HttpResponseBadRequest('الكمية غير متوفرة')
                        # build existing items map (description -> qty) before deleting
                        existing_items_map = {}
                        try:
                            for ex in InvoiceItem.objects.filter(invoice=invoice):
                                k = (ex.description or '').strip().lower()
                                try:
                                    existing_items_map[k] = existing_items_map.get(k, Decimal('0')) + Decimal(str(ex.quantity or 0))
                                except Exception:
                                    existing_items_map[k] = existing_items_map.get(k, Decimal('0'))
                        except Exception:
                            existing_items_map = {}

                        # Centralized availability check + transactional update
                        try:
                            import logging
                            logger = logging.getLogger('inventory')
                            logger.info('edit_invoice payload (raw): %s', data)
                        except Exception:
                            logger = None

                        # Normalize incoming items: support both description and part_id payloads
                        normalized = []
                        part_ids = set()
                        try:
                            from inventory.utils import find_part_for_description, check_items_availability, apply_inventory_changes_for_invoice
                            from inventory.models import Part
                            for it in data:
                                desc = (it.get('description') or '').strip()
                                pid = it.get('part_id') or it.get('part') or None
                                part = None
                                if pid:
                                    try:
                                        part = Part.objects.filter(id=int(pid)).first()
                                        if part:
                                            desc = part.name
                                            part_ids.add(part.id)
                                    except Exception:
                                        part = None
                                if not part and desc:
                                    part = find_part_for_description(desc)
                                    if part:
                                        part_ids.add(part.id)

                                try:
                                    q = Decimal(str(it.get('qty', 0) or 0))
                                except Exception:
                                    q = Decimal('0')
                                try:
                                    r = Decimal(str(it.get('rate', 0) or 0))
                                except Exception:
                                    r = Decimal('0')
                                try:
                                    d = Decimal(str(it.get('disc', 0) or 0))
                                except Exception:
                                    d = Decimal('0')
                                normalized.append({'description': desc, 'qty': q, 'rate': r, 'disc': d, 'part_id': (part.id if part else None)})
                        except Exception:
                            normalized = data

                        try:
                            from django.db import transaction
                            from django.contrib import messages
                            from django.http import HttpResponseBadRequest

                            shortages = check_items_availability(normalized, existing_items_map)
                            if shortages:
                                first = shortages[0]
                                pname = getattr(first[0], 'name', '') if first and first[0] else ''
                                msg = f'الكمية غير متوفرة: {pname}. المتوفر: {first[1]} المطلوب: {first[2]}'
                                messages.error(request, msg)
                                return HttpResponseBadRequest(msg)

                            # apply changes in a single atomic transaction: lock parts, delete old items, create new, update parts
                            with transaction.atomic():
                                try:
                                    if part_ids:
                                        Part.objects.select_for_update().filter(id__in=list(part_ids))
                                except Exception:
                                    pass

                                # restore inventory for existing invoice items before deleting them
                                try:
                                    from inventory.utils import apply_inventory_changes_for_invoice
                                    existing_items = []
                                    for ex in InvoiceItem.objects.filter(invoice=invoice):
                                        try:
                                            existing_items.append({'description': ex.description or '', 'qty': float(ex.quantity or 0)})
                                        except Exception:
                                            existing_items.append({'description': ex.description or '', 'qty': 0})
                                    if existing_items:
                                        try:
                                            apply_inventory_changes_for_invoice(existing_items, decrement=False)
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                                InvoiceItem.objects.filter(invoice=invoice).delete()
                                for it in normalized:
                                    desc = (it.get('description') or '').strip()
                                    q = it.get('qty', Decimal('0'))
                                    r = it.get('rate', Decimal('0'))
                                    d = it.get('disc', Decimal('0'))
                                    line_before = q * r
                                    line_disc = (line_before * d) / Decimal('100') if d else Decimal('0')
                                    line_total = (line_before - line_disc)
                                    if (not desc) and q == Decimal('0') and r == Decimal('0') and d == Decimal('0'):
                                        continue
                                    serv = None
                                    if desc:
                                        try:
                                            serv = ServiceModel.objects.filter(name__iexact=desc).first()
                                        except Exception:
                                            serv = None
                                    try:
                                        InvoiceItem.objects.create(
                                            invoice=invoice,
                                            service=serv,
                                            description=desc,
                                            quantity=q,
                                            rate=r,
                                            discount=d,
                                            total=line_total
                                        )
                                    except Exception:
                                        raise

                                try:
                                    apply_inventory_changes_for_invoice(normalized, decrement=True)
                                except Exception:
                                    raise
                        except Exception:
                            # if anything unexpected happens, abort and surface a generic message
                            from django.contrib import messages
                            messages.error(request, 'فشل في حفظ عناصر الفاتورة. حاول لاحقاً.')
                            return redirect('edit_invoice', invoice_id=invoice.id)
                    except Exception:
                        pass
                invoice.amount = float(computed_total)
                updated = True
            except Exception:
                pass

        # Update created_at if provided
        if created:
            try:
                from django.utils.dateparse import parse_datetime, parse_date
                dt = None
                try:
                    dt = parse_datetime(created)
                except Exception:
                    dt = None
                if not dt:
                    d = parse_date(created)
                    if d:
                        from datetime import datetime, time
                        dt = datetime.combine(d, time(12, 0))
                if dt:
                    invoice.created_at = dt
                    updated = True
            except Exception:
                pass

                # Save subject if provided (single-line subject field)
                try:
                    subj = request.POST.get('subject')
                    if subj is not None:
                        invoice.subject = subj
                        updated = True
                except Exception:
                    pass

        # Re-evaluate payment status: mark paid if received >= invoice.amount
        try:
            paid_amount = invoice.payments.filter(status='paid').aggregate(total=models.Sum('amount'))['total'] or 0
            # Compare as Decimal for safety
            from decimal import Decimal
            if updated:
                total_due = Decimal(str(invoice.amount or 0))
            else:
                total_due = Decimal(str(invoice.amount or 0))
            if Decimal(str(paid_amount or 0)) >= total_due and total_due > 0:
                invoice.paid = True
            else:
                invoice.paid = False
        except Exception:
            pass

        from django.contrib import messages
        # if caller requested a recalc-only action, persist and return to edit page
        if updated:
            invoice.save()
            messages.success(request, 'Invoice updated successfully.')
        else:
            messages.warning(request, 'No changes detected or invalid input.')

        action = request.POST.get('action', '').strip().lower()
        if action == 'recalculate':
            # go back to the same edit page so user can review persisted totals
            return redirect('edit_invoice', invoice_id=invoice.id)
        return redirect('invoices_list')
    # GET: render simplified edit page
    # Provide clients and parts data to support the advanced invoice editor frontend
    try:
        from clients.models import Client
        clients = list(Client.objects.all())
    except Exception:
        clients = []
    try:
        from inventory.models import Part
        parts = list(Part.objects.all())
    except Exception:
        parts = []

    # Compute payment summaries for display
    try:
        paid_amount = invoice.payments.filter(status='paid').aggregate(total=models.Sum('amount'))['total'] or 0
    except Exception:
        paid_amount = 0
    amount_used_for_payments = paid_amount
    amount_refunded = 0
    try:
        amount_in_excess = float(paid_amount) - float(invoice.amount) if paid_amount else 0
        if amount_in_excess < 0:
            amount_in_excess = 0
    except Exception:
        amount_in_excess = 0
    try:
        remaining_balance = float(invoice.amount) - float(paid_amount)
        if remaining_balance < 0:
            remaining_balance = 0
    except Exception:
        remaining_balance = 0

    # Load persisted invoice items if present; otherwise build from invoice.services for backward compatibility
    invoice_items = []
    try:
        from .models import InvoiceItem
        items_qs = InvoiceItem.objects.filter(invoice=invoice).order_by('id')
        if items_qs.exists():
            for it in items_qs:
                invoice_items.append({
                    'id': it.id,
                    'description': it.description or (it.service.name if it.service else ''),
                    'qty': float(it.quantity),
                    'rate': float(it.rate),
                    'disc': float(it.discount),
                    'amount': float(it.total),
                })
        else:
            for s in invoice.services.all():
                invoice_items.append({
                    'id': None,
                    'description': s.name,
                    'qty': 1,
                    'rate': float(getattr(s, 'default_price', 0) or 0),
                    'disc': 0,
                    'amount': float(getattr(s, 'default_price', 0) or 0),
                })
    except Exception:
        invoice_items = []

    # compute items_total and basic consistency warnings to help debug
    items_total = 0
    warnings = []
    try:
        from decimal import Decimal
        items_total = Decimal('0')
        for it in invoice_items:
            items_total += Decimal(str(it.get('amount') or 0))
        # compare item total vs invoice.amount
        try:
            inv_amount = Decimal(str(invoice.amount or 0))
            if items_total != inv_amount:
                warnings.append(f"Items total ({items_total}) != Invoice.amount ({inv_amount})")
        except Exception:
            pass
        # paid vs remaining check
        try:
            paid_amt = Decimal(str(paid_amount or 0))
            if invoice.paid and (paid_amt < Decimal(str(invoice.amount or 0))):
                warnings.append('Invoice is marked PAID but paid amount is less than invoice amount')
            if (not invoice.paid) and (paid_amt >= Decimal(str(invoice.amount or 0))) and invoice.amount > 0:
                warnings.append('Invoice is not marked PAID but paid amount >= invoice amount')
        except Exception:
            pass
    except Exception:
        items_total = 0

    return render(request, 'edit_invoice.html', {
        'invoice': invoice,
        'clients': clients,
        'parts': parts,
        'paid_amount': paid_amount,
        'amount_used_for_payments': amount_used_for_payments,
        'amount_refunded': amount_refunded,
        'amount_in_excess': amount_in_excess,
        'remaining_balance': remaining_balance,
        'invoice_items': invoice_items,
        'items_total': items_total,
        'debug_warnings': warnings,
    })
@login_required
def invoices_list(request):
    from .models import Invoice
    from django.db.models import Sum
    from django.utils.dateparse import parse_date
    invoices = Invoice.objects.select_related('client', 'car').order_by('-created_at')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    # General search q: matches invoice number, client name, or car plate (including client's other cars)
    q = (request.GET.get('q') or '').strip()
    car_number = (request.GET.get('car_number') or '').strip()
    invoice_number_q = (request.GET.get('invoice_number') or '').strip()
    if start_date:
        invoices = invoices.filter(created_at__date__gte=parse_date(start_date))
    if end_date:
        invoices = invoices.filter(created_at__date__lte=parse_date(end_date))
    # Apply search filters
    try:
        from clients.models import Client
        if q:
            # search clients by name/phone/customer id or invoices' car plate
            client_qs = Client.objects.filter(
                models.Q(first_name__icontains=q) |
                models.Q(last_name__icontains=q) |
                models.Q(phone_number__icontains=q) |
                models.Q(customer_id__icontains=q) |
                models.Q(cars__plate_number__icontains=q)
            ).distinct()
            if client_qs.exists():
                invoices = invoices.filter(models.Q(client__in=client_qs) | models.Q(car__plate_number__icontains=q)).distinct()
            else:
                invoices = invoices.filter(models.Q(car__plate_number__icontains=q) | models.Q(invoice_number__icontains=q)).distinct()
        if car_number:
            # include invoices where the invoice.car matches OR the client has a car with that plate
            client_qs2 = Client.objects.filter(cars__plate_number__icontains=car_number).distinct()
            invoices = invoices.filter(models.Q(car__plate_number__icontains=car_number) | models.Q(client__in=client_qs2)).distinct()
        if invoice_number_q:
            invoices = invoices.filter(invoice_number__icontains=invoice_number_q)
    except Exception:
        # best-effort: ignore search errors and continue
        pass
    total_amount = invoices.aggregate(total=Sum('amount'))['total'] or 0

    # Pagination / per-page handling
    per_page_param = request.GET.get('per_page', '').strip()
    per_page_options = [25, 50, 100, 200, 'all']
    try:
        if per_page_param.lower() == 'all' or per_page_param == '0':
            per_page = 0
        elif per_page_param:
            per_page = int(per_page_param)
        else:
            per_page = 25
    except Exception:
        per_page = 25

    page_obj = None
    if per_page and per_page > 0:
        paginator = Paginator(invoices, per_page)
        page_num = request.GET.get('page', 1)
        try:
            page_obj = paginator.get_page(page_num)
            invoices = page_obj
        except Exception:
            page_obj = paginator.get_page(1)
            invoices = page_obj
    else:
        # per_page == 0 means show all (no pagination)
        page_obj = None

    # annotate invoices with paid_amount for partial/paid display
    try:
        for inv in invoices:
            try:
                inv.paid_amount = inv.payments.filter(status='paid').aggregate(total=models.Sum('amount'))['total'] or 0
            except Exception:
                inv.paid_amount = 0
            # annotate delivery_date from related maintenance records (most recent non-null delivery)
            try:
                from cars.maintenance_models import MaintenanceRecord
                last_del = MaintenanceRecord.objects.filter(invoice=inv, delivery_date__isnull=False).order_by('-delivery_date').values_list('delivery_date', flat=True).first()
                inv.delivery_date = last_del
            except Exception:
                inv.delivery_date = None
    except Exception:
        pass

    # Ensure the template receives a concrete list ordered by `id` desc
    try:
        iterable = invoices.object_list if hasattr(invoices, 'object_list') else invoices
        invoices_sorted = sorted(list(iterable), key=lambda x: getattr(x, 'id', 0), reverse=True)
    except Exception:
        invoices_sorted = invoices

    return render(request, 'invoices_list.html', {
        'invoices': invoices_sorted,
        'start_date': start_date,
        'end_date': end_date,
        'total_amount': total_amount,
        'page_obj': page_obj,
        'per_page': per_page,
        'per_page_options': per_page_options,
    })
from django.contrib import messages


@login_required
def bulk_delete_invoices(request):
    from django.http import JsonResponse, HttpResponseBadRequest
    import json
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid method')
    try:
        data = json.loads(request.body.decode('utf-8') or '[]')
    except Exception:
        return HttpResponseBadRequest('Invalid payload')
    ids = []
    try:
        for v in data:
            try:
                ids.append(int(v))
            except Exception:
                continue
    except Exception:
        return HttpResponseBadRequest('Invalid payload')

    deleted = []
    skipped = []
    from cars.maintenance_models import MaintenanceRecord
    try:
        from inventory.utils import apply_inventory_changes_for_invoice
    except Exception:
        apply_inventory_changes_for_invoice = None
    for iid in ids:
        try:
            inv = Invoice.objects.get(id=iid)
        except Exception:
            skipped.append({'id': iid, 'reason': 'not_found'})
            continue
        try:
            if MaintenanceRecord.objects.filter(invoice=inv).exists():
                skipped.append({'id': iid, 'reason': 'has_maintenance'})
                continue
        except Exception:
            pass
        # restore inventory for items
        try:
            existing_items = []
            for it in inv.items.all():
                try:
                    existing_items.append({'description': it.description or '', 'qty': float(it.quantity or 0)})
                except Exception:
                    existing_items.append({'description': it.description or '', 'qty': 0})
            if existing_items and apply_inventory_changes_for_invoice:
                try:
                    apply_inventory_changes_for_invoice(existing_items, decrement=False)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            inv.delete()
            deleted.append(iid)
        except Exception:
            skipped.append({'id': iid, 'reason': 'delete_failed'})

    return JsonResponse({'deleted': deleted, 'skipped': skipped})


@login_required
def client_invoices_json(request, client_id):
    from django.http import JsonResponse
    try:
        # only include invoices with remaining balance > 0 (unpaid or partially paid)
        invs = Invoice.objects.filter(client_id=client_id).order_by('-created_at')
    except Exception:
        return JsonResponse([], safe=False)
    out = []
    for inv in invs:
        try:
            paid_amount = inv.payments.filter(status='paid').aggregate(total=models.Sum('amount'))['total'] or 0
        except Exception:
            paid_amount = 0
        try:
            amt = float(inv.amount or 0)
        except Exception:
            amt = 0.0
        try:
            paid = float(paid_amount or 0)
        except Exception:
            paid = 0.0
        remaining = max(0.0, amt - paid)
        if remaining <= 0:
            # skip fully paid invoices
            continue
        out.append({
            'id': inv.id,
            'invoice_number': inv.invoice_number,
            'date': inv.created_at.strftime('%Y-%m-%d') if inv.created_at else '',
            'amount': amt,
            'paid': paid,
            'remaining': remaining,
        })
    return JsonResponse(out, safe=False)


@login_required
def get_invoice_json(request, invoice_id):
    from django.http import JsonResponse
    try:
        inv = Invoice.objects.select_related('client').get(id=invoice_id)
    except Exception:
        return JsonResponse({'error': 'not_found'}, status=404)
    try:
        paid_amount = inv.payments.filter(status='paid').aggregate(total=models.Sum('amount'))['total'] or 0
    except Exception:
        paid_amount = 0
    try:
        amt = float(inv.amount or 0)
    except Exception:
        amt = 0.0
    remaining = max(0.0, amt - float(paid_amount or 0))
    return JsonResponse({
        'id': inv.id,
        'invoice_number': inv.invoice_number,
        'client_id': inv.client.id if inv.client else None,
        'client_name': f"{inv.client.first_name} {(inv.client.last_name or '')}".strip() if inv.client else '',
        'amount': amt,
        'remaining': remaining,
        'date': inv.created_at.strftime('%Y-%m-%d') if inv.created_at else ''
    })


@login_required
def add_payment(request):
    from django.http import JsonResponse, HttpResponseBadRequest
    from clients.models import Client
    from decimal import Decimal
    from django.utils import timezone
    from .models import Payment

    if request.method == 'POST':
        client_id = request.POST.get('client_id')
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
            client = Client.objects.get(id=int(client_id))
        except Exception:
            return HttpResponseBadRequest('عميل غير موجود')

        # parse payment_date
        try:
            if payment_date:
                pd = parse_date(payment_date)
                from datetime import datetime, time
                payment_dt = datetime.combine(pd, time(12, 0))
            else:
                payment_dt = timezone.now()
        except Exception:
            payment_dt = timezone.now()

        draft_flag = request.POST.get('draft') in ('1', 'true', 'yes') or request.POST.get('action') == 'save_draft'
        created_payments = []
        try:
            for a in alloc:
                inv_id = a.get('invoice_id')
                amt = a.get('amount')
                try:
                    amt_val = Decimal(str(amt or 0))
                except Exception:
                    amt_val = Decimal('0')
                if amt_val <= 0:
                    continue
                try:
                    inv = Invoice.objects.get(id=int(inv_id))
                except Exception:
                    continue
                # create payment record; if draft, mark payment as 'unpaid' so it doesn't affect invoice balances
                p = Payment.objects.create(
                    invoice=inv,
                    car=inv.car,
                    client=client,
                    amount=float(amt_val),
                    status=('unpaid' if draft_flag else 'paid'),
                    payment_date=payment_dt,
                    method=method or 'cash',
                    reference=reference,
                    notes=notes,
                )
                created_payments.append(p.id)
                # update invoice paid flag only when not saving as draft
                if not draft_flag:
                    try:
                        paid_amount = inv.payments.filter(status='paid').aggregate(total=models.Sum('amount'))['total'] or 0
                        from decimal import Decimal as D
                        if D(str(paid_amount or 0)) >= D(str(inv.amount or 0)) and float(inv.amount or 0) > 0:
                            inv.paid = True
                        else:
                            inv.paid = False
                        inv.save()
                    except Exception:
                        pass
        except Exception as e:
            return HttpResponseBadRequest('فشل في معالجة المدفوعات: ' + str(e))

        return JsonResponse({'created': created_payments})

    # GET -> render page
    try:
        clients = list(Client.objects.all().order_by('first_name')[:500])
    except Exception:
        clients = []

    # compute next payment reference (e.g. 202600001) using year + sequence
    next_payment_ref = ''
    try:
        from .models import Payment
        last = Payment.objects.order_by('-id').first()
        import datetime
        year = datetime.datetime.now().year
        if last and getattr(last, 'reference', None):
            ref = str(last.reference).strip()
            # if ref starts with current year digits and rest is numeric, increment
            if ref.startswith(str(year)) and ref[len(str(year)):].isdigit():
                try:
                    tail = int(ref[len(str(year)):]) + 1
                    next_payment_ref = f"{year}{tail:06d}"
                except Exception:
                    next_payment_ref = f"{year}000001"
            else:
                # try to find trailing number
                import re
                m = re.search(r"(\d+)$", ref)
                if m:
                    try:
                        num = int(m.group(1)) + 1
                        # keep same width
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

    return render(request, 'payments_add.html', {'clients': clients, 'next_payment_ref': next_payment_ref})

# حذف الفاتورة إذا لم يكن لها سجلات صيانة مرتبطة
@login_required
def delete_invoice(request, invoice_id):
    from cars.maintenance_models import MaintenanceRecord
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if MaintenanceRecord.objects.filter(invoice=invoice).exists():
        messages.error(request, "Cannot delete invoice: maintenance records are linked to it.")
        return redirect('cars:maintenance_list')
    if request.method == 'POST':
        # restore inventory for this invoice's items before deleting the invoice
        try:
            from inventory.utils import apply_inventory_changes_for_invoice
            existing_items = []
            try:
                for it in invoice.items.all():
                    try:
                        existing_items.append({'description': it.description or '', 'qty': float(it.quantity or 0)})
                    except Exception:
                        existing_items.append({'description': it.description or '', 'qty': 0})
            except Exception:
                existing_items = []
            if existing_items:
                try:
                    apply_inventory_changes_for_invoice(existing_items, decrement=False)
                except Exception:
                    pass
        except Exception:
            pass
        invoice.delete()
        messages.success(request, "Invoice deleted successfully.")
        return redirect('cars:maintenance_list')
    return render(request, 'delete_invoice.html', {'invoice': invoice})

@login_required
def pay_invoice_by_id(request, invoice_id):
    from cars.models import Car
    try:
        invoice = Invoice.objects.get(id=invoice_id)
        car = invoice.car
        if invoice.paid:
            return render(request, 'invoice_already_paid.html', {'invoice': invoice, 'car': car})
    except Invoice.DoesNotExist:
        from django.contrib import messages
        messages.error(request, "لا توجد فاتورة بهذا الرقم.")
        return redirect('cars:cars_list')
    # جلب تاريخ أول سجل صيانة مرتبط بهذه الفاتورة (إن وجد)
    from cars.maintenance_models import MaintenanceRecord
    maintenance_date = MaintenanceRecord.objects.filter(invoice=invoice).order_by('created_at').values_list('created_at', flat=True).first()
    # Cleanup any completely-empty invoice items (total zero AND no description and no service)
    try:
        from django.db.models import Q
        empty_items_qs = invoice.items.filter(Q(total__lte=0) & (Q(description__isnull=True) | Q(description='')) & Q(service__isnull=True))
        if empty_items_qs.exists():
            try:
                # delete them to avoid showing blank rows on payment page
                empty_items_qs.delete()
            except Exception:
                pass
    except Exception:
        pass
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment_date = form.cleaned_data['payment_date']
            from datetime import datetime, time
            if isinstance(payment_date, datetime):
                payment_datetime = payment_date
            else:
                payment_datetime = datetime.combine(payment_date, time(12, 0))
            method = form.cleaned_data['method']
            reference = form.cleaned_data['reference']
            notes = form.cleaned_data['notes']
            pay_amount = form.cleaned_data.get('amount')
            if method == 'benefit' and not reference:
                last_payment = Payment.objects.filter(method='benefit').order_by('-id').first()
                if last_payment and last_payment.reference and last_payment.reference.isdigit():
                    next_ref = str(int(last_payment.reference) + 1).zfill(7)
                else:
                    next_ref = '0000001'
                reference = next_ref
            # determine amount: prefer explicit amount from form (partial payment), else use invoice.amount
            try:
                if pay_amount not in (None, ''):
                    amt_val = float(pay_amount)
                else:
                    amt_val = float(invoice.amount)
            except Exception:
                amt_val = float(invoice.amount)

            Payment.objects.create(
                invoice=invoice,
                car=car,
                client=car.client,
                amount=amt_val,
                status='paid',
                payment_date=payment_datetime,
                method=method,
                notes=notes,
                reference=reference
            )
            # recompute paid flag after adding this payment
            invoice.save()
            # تحديث حالة السيارة إلى مدفوعة بانتظار الاستلام
            car.status = 'paid_waiting_collection'
            car.save()
            # حساب المبلغ المدفوع والرصيد المتبقي
            paid_amount = invoice.payments.filter(status='paid').aggregate(total=models.Sum('amount'))['total'] or 0
            # update invoice.paid based on paid_amount vs invoice.amount
            try:
                from decimal import Decimal
                if Decimal(str(paid_amount or 0)) >= Decimal(str(invoice.amount or 0)) and float(invoice.amount or 0) > 0:
                    invoice.paid = True
                else:
                    invoice.paid = False
                invoice.save()
            except Exception:
                pass
            remaining_balance = float(invoice.amount) - float(paid_amount)
            return render(request, 'payment_success.html', {
                'car': car,
                'invoice': invoice,
                'paid_amount': paid_amount,
                'remaining_balance': remaining_balance,
            })
    else:
        initial = {}
        # Always prepare a next benefit reference (useful to display even if method not preselected)
        try:
            from .models import Payment as PaymentModel
            last_payment = PaymentModel.objects.filter(method='benefit').order_by('-id').first()
            if last_payment and last_payment.reference and last_payment.reference.isdigit():
                next_ref = str(int(last_payment.reference) + 1).zfill(7)
            else:
                next_ref = '0000001'
        except Exception:
            next_ref = '0000001'

        if request.GET.get('method') == 'benefit':
            initial['reference'] = next_ref
        else:
            # if not prefilled, show the suggested next reference so user can see numbering
            initial.setdefault('reference', next_ref)
        # Prefill amount if provided via GET (e.g., ?amount=10.000) or compute remaining_balance
        try:
            amt_q = request.GET.get('amount')
            if amt_q:
                initial['amount'] = amt_q
            else:
                # compute remaining_balance
                paid_amount = invoice.payments.filter(status='paid').aggregate(total=models.Sum('amount'))['total'] or 0
                remaining_balance = float(invoice.amount) - float(paid_amount)
                if remaining_balance > 0:
                    initial['amount'] = remaining_balance
        except Exception:
            pass
        # Prepare cleaned invoice items for rendering (exclude any zero-total rows)
        try:
            invoice_items_qs = invoice.items.filter(total__gt=0)
        except Exception:
            invoice_items_qs = invoice.items.all()
        form = PaymentForm(initial=initial)
    return render(request, 'pay_invoice.html', {'form': form, 'car': car, 'invoice': invoice, 'maintenance_date': maintenance_date, 'invoice_items_qs': invoice_items_qs})
from django.shortcuts import render, get_object_or_404, redirect
from .models import Invoice, Payment
from cars.models import Car
from django.urls import reverse

from .forms import PaymentForm
from django.utils import timezone
from django.utils.dateparse import parse_date

@login_required
def pay_invoice(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    invoice = Invoice.objects.filter(car=car, paid=False).first()
    if not invoice:
        return redirect(reverse('cars_list'))

    # جلب تاريخ أول سجل صيانة مرتبط بهذه الفاتورة (إن وجد)
    from cars.maintenance_models import MaintenanceRecord
    maintenance_date = MaintenanceRecord.objects.filter(invoice=invoice).order_by('created_at').values_list('created_at', flat=True).first()

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment_date = form.cleaned_data['payment_date']
            # تحويل التاريخ إلى datetime مع وقت افتراضي 12:00
            from datetime import datetime, time
            if isinstance(payment_date, datetime):
                payment_datetime = payment_date
            else:
                payment_datetime = datetime.combine(payment_date, time(12, 0))
            method = form.cleaned_data['method']
            reference = form.cleaned_data['reference']
            notes = form.cleaned_data['notes']
            # إذا طريقة الدفع بنفت ولم يدخل المستخدم رقم مرجع، نولده تلقائياً
            if method == 'benefit' and not reference:
                last_payment = Payment.objects.filter(method='benefit').order_by('-id').first()
                if last_payment and last_payment.reference and last_payment.reference.isdigit():
                    next_ref = str(int(last_payment.reference) + 1).zfill(7)
                else:
                    next_ref = '0000001'
                reference = next_ref
            pay_amount = form.cleaned_data.get('amount')
            try:
                if pay_amount not in (None, ''):
                    amt_val = float(pay_amount)
                else:
                    amt_val = float(invoice.amount)
            except Exception:
                amt_val = float(invoice.amount)

            Payment.objects.create(
                invoice=invoice,
                car=car,
                client=car.client,
                amount=amt_val,
                status='paid',
                payment_date=payment_datetime,
                method=method,
                notes=notes,
                reference=reference
            )
            # recalc invoice paid status
            try:
                from decimal import Decimal
                paid_amount = invoice.payments.filter(status='paid').aggregate(total=models.Sum('amount'))['total'] or 0
                if Decimal(str(paid_amount or 0)) >= Decimal(str(invoice.amount or 0)) and float(invoice.amount or 0) > 0:
                    invoice.paid = True
                else:
                    invoice.paid = False
                invoice.save()
            except Exception:
                invoice.paid = invoice.paid
            # تحديث حالة السيارة إلى مدفوعة بانتظار الاستلام بعد الدفع
            car.status = 'paid_waiting_collection'
            car.save()
            # تعليم جميع سجلات الصيانة كمُنتهية
            from cars.maintenance_models import MaintenanceRecord
            MaintenanceRecord.objects.filter(car=car, is_finished=False).update(is_finished=True, ready_at=None)
            # بعد الدفع، اعرض صفحة تأكيد مع تفاصيل الفاتورة وزر طباعة
            # حساب المبلغ المدفوع والرصيد المتبقي
            paid_amount = invoice.payments.filter(status='paid').aggregate(total=models.Sum('amount'))['total'] or 0
            remaining_balance = invoice.amount - paid_amount
            return render(request, 'payment_success.html', {
                'car': car,
                'invoice': invoice,
                'paid_amount': paid_amount,
                'remaining_balance': remaining_balance,
            })
    else:
        # توليد رقم مرجع افتراضي في الفورم إذا كانت أول مرة وبنفت
        initial = {'amount': remaining_balance}
        if request.GET.get('method') == 'benefit':
            last_payment = Payment.objects.filter(method='benefit').order_by('-id').first()
            if last_payment and last_payment.reference and last_payment.reference.isdigit():
                next_ref = str(int(last_payment.reference) + 1).zfill(7)
            else:
                next_ref = '0000001'
            initial['reference'] = next_ref
        form = PaymentForm(initial=initial)

    return render(request, 'pay_invoice.html', {
        'form': form,
        'car': car,
        'invoice': invoice,
        'maintenance_date': maintenance_date,
        'paid_amount': paid_amount,
        'remaining_balance': remaining_balance,
        'amount_refunded': amount_refunded,
        'amount_in_excess': amount_in_excess,
    })

@login_required
def payments_list(request):
    payments_qs = Payment.objects.filter(status='paid').select_related('client', 'car', 'invoice')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        payments_qs = payments_qs.filter(payment_date__date__gte=parse_date(start_date))
    if end_date:
        payments_qs = payments_qs.filter(payment_date__date__lte=parse_date(end_date))
    payments_qs = payments_qs.order_by('invoice__invoice_number')

    # Build a serializable list including computed unused amount per payment
    payments = []
    # English label mappings for method/status (keep model choices as-is)
    STATUS_LABELS_EN = {
        'paid': 'Paid',
        'unpaid': 'Unpaid',
        'partial': 'Partial',
    }
    METHOD_LABELS_EN = {
        'cash': 'Cash',
        'card': 'Card',
        'benefit': 'Benefit',
        'bank': 'Bank Transfer',
        'other': 'Other',
    }
    from django.db.models import Sum
    for p in payments_qs:
        try:
            # sum of other paid payments on the same invoice (before/aside from this payment)
            paid_others = p.invoice.payments.filter(status='paid').exclude(id=p.id).aggregate(total=Sum('amount'))['total'] or 0
        except Exception:
            paid_others = 0
        try:
            invoice_total = float(p.invoice.amount or 0)
        except Exception:
            invoice_total = 0.0
        try:
            paid_others_f = float(paid_others or 0)
        except Exception:
            paid_others_f = 0.0
        remaining_before = max(0.0, invoice_total - paid_others_f)
        try:
            payment_amount = float(p.amount or 0)
        except Exception:
            payment_amount = 0.0
        amount_applied = min(payment_amount, remaining_before)
        unused_amount = round(max(0.0, payment_amount - amount_applied), 3)
        payments.append({
            'id': p.id,
            'client_name': (p.client.first_name or '') + ((' ' + p.client.last_name) if getattr(p.client, 'last_name', None) else ''),
            'payment_date': p.payment_date,
            'reference': p.reference,
            'method': METHOD_LABELS_EN.get(p.method, p.get_method_display() if hasattr(p, 'get_method_display') else p.method),
            'status': STATUS_LABELS_EN.get(p.status, p.get_status_display() if hasattr(p, 'get_status_display') else p.status),
            'amount': payment_amount,
            'unused': unused_amount,
        })

    # Calculate total amount
    total_amount = sum([x.get('amount', 0) for x in payments])

    # Pagination / per-page handling (match invoices_list pattern)
    per_page_param = request.GET.get('per_page', '').strip()
    per_page_options = [25, 50, 100, 200, 'all']
    try:
        if per_page_param.lower() == 'all' or per_page_param == '0':
            per_page = 0
        elif per_page_param:
            per_page = int(per_page_param)
        else:
            per_page = 25
    except Exception:
        per_page = 25

    page_obj = None
    if per_page and per_page > 0:
        paginator = Paginator(payments, per_page)
        page_num = request.GET.get('page', 1)
        try:
            page_obj = paginator.get_page(page_num)
            payments = page_obj
        except Exception:
            page_obj = paginator.get_page(1)
            payments = page_obj
    else:
        # per_page == 0 means show all (no pagination)
        page_obj = None

    return render(request, 'payments_list.html', {
        'payments': payments,
        'start_date': start_date,
        'end_date': end_date,
        'total_amount': total_amount,
        'page_obj': page_obj,
        'per_page': per_page,
        'per_page_options': per_page_options,
        'search': None,
    })

@login_required
def invoices_due_list(request):
    invoices = Invoice.objects.filter(paid=False).select_related('client', 'car')
    return render(request, 'invoices_due_list.html', {'invoices': invoices})

@login_required
def edit_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    if request.method == 'POST':
        new_date = request.POST.get('payment_date')
        if new_date:
            payment.payment_date = new_date
            payment.save()
            return redirect('payments_list')
    return render(request, 'edit_payment.html', {'payment': payment})


@login_required
def delete_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    invoice = payment.invoice
    if request.method == 'POST':
        payment.delete()
        # Recalculate invoice paid status
        try:
            paid_amount = invoice.payments.filter(status='paid').aggregate(total=models.Sum('amount'))['total'] or 0
            from decimal import Decimal
            if Decimal(str(paid_amount or 0)) >= Decimal(str(invoice.amount or 0)) and float(invoice.amount or 0) > 0:
                invoice.paid = True
            else:
                invoice.paid = False
            invoice.save()
        except Exception:
            pass
        from django.contrib import messages
        messages.success(request, 'Payment deleted.')
        return redirect('payments_list')
    return render(request, 'confirm_delete_payment.html', {'payment': payment, 'invoice': invoice})
