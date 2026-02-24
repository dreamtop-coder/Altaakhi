
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Invoice
from django.core.paginator import Paginator
from django.db import models

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
    invoices = Invoice.objects.select_related('client', 'car').order_by('-created_at')
    car_number = request.GET.get('car_number', '').strip()
    invoice_number = request.GET.get('invoice_number', '').strip()
    if car_number:
        invoices = invoices.filter(car__plate_number__icontains=car_number)
    if invoice_number:
        invoices = invoices.filter(invoice_number__icontains=invoice_number)
    return render(request, 'invoices_print_list.html', {'invoices': invoices})
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
                        InvoiceItem.objects.filter(invoice=invoice).delete()
                        for it in data:
                            desc = (it.get('description') or '').strip()
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
                            line_before = q * r
                            line_disc = (line_before * d) / Decimal('100') if d else Decimal('0')
                            line_total = (line_before - line_disc)
                            # Skip completely empty rows (no description and no numeric values)
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
                                pass
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
    per_page_options = [25, 50, 100, 200]
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

    return render(request, 'invoices_list.html', {
        'invoices': invoices,
        'start_date': start_date,
        'end_date': end_date,
        'total_amount': total_amount,
        'page_obj': page_obj,
        'per_page': per_page,
        'per_page_options': per_page_options,
    })
from django.contrib import messages

# حذف الفاتورة إذا لم يكن لها سجلات صيانة مرتبطة
@login_required
def delete_invoice(request, invoice_id):
    from cars.maintenance_models import MaintenanceRecord
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if MaintenanceRecord.objects.filter(invoice=invoice).exists():
        messages.error(request, "لا يمكن حذف الفاتورة لوجود سجلات صيانة مرتبطة بها.")
        return redirect('cars:maintenance_list')
    if request.method == 'POST':
        invoice.delete()
        messages.success(request, "تم حذف الفاتورة بنجاح.")
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
        if request.GET.get('method') == 'benefit':
            last_payment = Payment.objects.filter(method='benefit').order_by('-id').first()
            if last_payment and last_payment.reference and last_payment.reference.isdigit():
                next_ref = str(int(last_payment.reference) + 1).zfill(7)
            else:
                next_ref = '0000001'
            initial['reference'] = next_ref
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
    payments = Payment.objects.filter(status='paid').select_related('client', 'car', 'invoice')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        payments = payments.filter(payment_date__date__gte=parse_date(start_date))
    if end_date:
        payments = payments.filter(payment_date__date__lte=parse_date(end_date))
    payments = payments.order_by('invoice__invoice_number')
    # Calculate total amount
    total_amount = payments.aggregate(total=models.Sum('amount'))['total'] or 0
    return render(request, 'payments_list.html', {
        'payments': payments,
        'start_date': start_date,
        'end_date': end_date,
        'total_amount': total_amount,
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
