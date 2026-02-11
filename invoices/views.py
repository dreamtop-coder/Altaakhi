from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.contrib import messages
from datetime import datetime, time
from django.forms import modelformset_factory
from django.db import transaction
from cars.forms_edit_maintenance import EditMaintenanceRecordForm
from decimal import Decimal

from .models import Invoice, Payment
from .forms import EditInvoiceForm, PaymentForm
from cars.models import Car
from cars.maintenance_models import MaintenanceRecord
from clients.models import Client



# كشف حساب عميل (للطباعة)
@login_required
def account_statement_print_view(request):
    client = None
    invoices = []
    query = request.GET.get("q", "").strip()
    if query:
        clients = Client.objects.filter(
            models.Q(first_name__icontains=query)
            | models.Q(last_name__icontains=query)
            | models.Q(phone_number__icontains=query)
            | models.Q(customer_id__icontains=query)
            | models.Q(invoices__car__plate_number__icontains=query)
        ).distinct()
        if clients.exists():
            client = clients.first()
            invoices = client.invoices.select_related("car").order_by("-created_at")
    return render(
        request,
        "account_statement_print.html",
        {"client": client, "invoices": invoices, "query": query},
    )


# كشف حساب عميل
@login_required
def account_statement_view(request):
    client = None
    invoices = []
    query = request.GET.get("q", "").strip()
    from_date = request.GET.get("from_date", "").strip()
    to_date = request.GET.get("to_date", "").strip()
    if query:
        # البحث بالاسم أو رقم الهاتف أو رقم العميل أو رقم السيارة
        clients = Client.objects.filter(
            models.Q(first_name__icontains=query)
            | models.Q(last_name__icontains=query)
            | models.Q(phone_number__icontains=query)
            | models.Q(customer_id__icontains=query)
            | models.Q(invoices__car__plate_number__icontains=query)
        ).distinct()
        if clients.exists():
            client = clients.first()
            invoices = client.invoices.select_related("car").order_by("-created_at")
            # فلترة بالتواريخ
            if from_date:
                invoices = invoices.filter(created_at__gte=from_date)
            if to_date:
                invoices = invoices.filter(created_at__lte=to_date)
            client.invoices.prefetch_related("payments")
    return render(
        request,
        "account_statement.html",
        {
            "client": client,
            "invoices": invoices,
            "query": query,
            "from_date": from_date,
            "to_date": to_date,
        },
    )


# طباعة فاتورة واحدة
@login_required
def print_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    return render(request, "payment_success.html", {"invoice": invoice})


@login_required
def invoices_print_list(request):
    invoices = Invoice.objects.select_related("client", "car").order_by("-created_at")
    car_number = request.GET.get("car_number", "").strip()
    invoice_number = request.GET.get("invoice_number", "").strip()
    if car_number:
        invoices = invoices.filter(car__plate_number__icontains=car_number)
    if invoice_number:
        invoices = invoices.filter(invoice_number__icontains=invoice_number)
    return render(request, "invoices_print_list.html", {"invoices": invoices})


# عرض وتعديل جماعي لسجلات الصيانة المرتبطة بفاتورة
@login_required
def edit_invoice_records(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    records = MaintenanceRecord.objects.filter(invoice=invoice).select_related("service")
    return render(request, "edit_invoice_records.html", {"invoice": invoice, "records": records})


# تعديل الفاتورة (المبلغ فقط حالياً)
@login_required
def edit_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.method == "POST":
        form = EditInvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            invoice = form.save(commit=False)
            if not invoice.created_at:
                invoice.created_at = timezone.now()
            invoice.save()
            messages.success(request, "تم تعديل الفاتورة بنجاح.")
            return redirect("invoices_list")
    else:
        form = EditInvoiceForm(instance=invoice)
    return render(request, "edit_invoice.html", {"form": form, "invoice": invoice})


@login_required
def invoices_list(request):
    invoices = Invoice.objects.select_related("client", "car").order_by("-created_at")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    if start_date:
        invoices = invoices.filter(created_at__date__gte=parse_date(start_date))
    if end_date:
        invoices = invoices.filter(created_at__date__lte=parse_date(end_date))
    total_amount = invoices.aggregate(total=Sum("amount"))["total"] or 0
    return render(
        request,
        "invoices_list.html",
        {
            "invoices": invoices,
            "start_date": start_date,
            "end_date": end_date,
            "total_amount": total_amount,
        },
    )


@login_required
def edit_invoice_full(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    MaintenanceFormSet = modelformset_factory(
        MaintenanceRecord, form=EditMaintenanceRecordForm, extra=0, can_delete=True
    )
    if request.method == "POST":
        form = EditInvoiceForm(request.POST, instance=invoice)
        formset = MaintenanceFormSet(
            request.POST, queryset=MaintenanceRecord.objects.filter(invoice=invoice)
        )
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                instances = formset.save(commit=False)
                for inst in instances:
                    inst.invoice = invoice
                    inst.save()
                for obj in formset.deleted_objects:
                    obj.delete()
            messages.success(request, "تم حفظ التعديلات على الفاتورة وسجلات الصيانة.")
            return redirect("invoices_list")
    else:
        form = EditInvoiceForm(instance=invoice)
        formset = MaintenanceFormSet(queryset=MaintenanceRecord.objects.filter(invoice=invoice))
    return render(request, "edit_invoice_full.html", {"form": form, "formset": formset, "invoice": invoice})


# حذف الفاتورة إذا لم يكن لها سجلات صيانة مرتبطة
@login_required
def delete_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if MaintenanceRecord.objects.filter(invoice=invoice).exists():
        messages.error(request, "لا يمكن حذف الفاتورة لوجود سجلات صيانة مرتبطة بها.")
        return redirect("cars:maintenance_list")
    if request.method == "POST":
        invoice.delete()
        messages.success(request, "تم حذف الفاتورة بنجاح.")
        return redirect("cars:maintenance_list")
    return render(request, "delete_invoice.html", {"invoice": invoice})


@login_required
def pay_invoice_by_id(request, invoice_id):
    try:
        invoice = Invoice.objects.get(id=invoice_id)
        car = invoice.car
        if invoice.paid:
            return render(request, "invoice_already_paid.html", {"invoice": invoice, "car": car})
    except Invoice.DoesNotExist:
        messages.error(request, "لا توجد فاتورة بهذا الرقم.")
        return redirect("cars:cars_list")

    maintenance_date = (
        MaintenanceRecord.objects.filter(invoice=invoice)
        .order_by("created_at")
        .values_list("created_at", flat=True)
        .first()
    )
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment_date = form.cleaned_data["payment_date"]

            if isinstance(payment_date, datetime):
                payment_datetime = payment_date
            else:
                payment_datetime = datetime.combine(payment_date, time(12, 0))
            method = form.cleaned_data["method"]
            reference = form.cleaned_data["reference"]
            notes = form.cleaned_data["notes"]
            if method == "benefit" and not reference:
                last_payment = (
                    Payment.objects.filter(method="benefit").order_by("-id").first()
                )
                if last_payment and last_payment.reference and last_payment.reference.isdigit():
                    next_ref = str(int(last_payment.reference) + 1).zfill(7)
                else:
                    next_ref = "0000001"
                reference = next_ref
            Payment.objects.create(
                invoice=invoice,
                car=car,
                client=car.client,
                amount=invoice.amount,
                status="paid",
                payment_date=payment_datetime,
                method=method,
                notes=notes,
                reference=reference,
            )
            invoice.paid = True
            invoice.save()
            # تحديث حالة السيارة إلى منتهية (sold)
            car.status = "sold"
            car.save()
            # حساب المبلغ المدفوع والرصيد المتبقي
            paid_amount = (
                invoice.payments.filter(status="paid").aggregate(total=models.Sum("amount"))["total"]
                or 0
            )
            remaining_balance = invoice.amount - paid_amount
            # collect parts for display
            invoice_parts = []
            parts_total = Decimal('0.00')
            for r in invoice.maintenance_records.all():
                for p in r.parts.all():
                    invoice_parts.append(p)
                    try:
                        parts_total += Decimal(str(p.total_price or 0))
                    except Exception:
                        parts_total += p.total_price or 0

            return render(
                request,
                "payment_success.html",
                {
                    "car": car,
                    "invoice": invoice,
                    "paid_amount": paid_amount,
                    "remaining_balance": remaining_balance,
                    "invoice_parts": invoice_parts,
                    "parts_total": parts_total,
                    "service_records": invoice.maintenance_records.filter(service__isnull=False),
                },
            )
    else:
        initial = {}
        if request.GET.get("method") == "benefit":
            last_payment = (
                Payment.objects.filter(method="benefit").order_by("-id").first()
            )
            if last_payment and last_payment.reference and last_payment.reference.isdigit():
                next_ref = str(int(last_payment.reference) + 1).zfill(7)
            else:
                next_ref = "0000001"
            initial["reference"] = next_ref
        form = PaymentForm(initial=initial)
    # collect parts across maintenance records for display and recompute invoice.amount
    invoice_parts = []
    parts_total = Decimal('0.00')
    for r in invoice.maintenance_records.all():
        for p in r.parts.all():
            invoice_parts.append(p)
            try:
                parts_total += Decimal(str(p.total_price or 0))
            except Exception:
                parts_total += Decimal(p.total_price or 0)

    # sum service prices only for records that have a linked service
    services_total = Decimal('0.00')
    for r in invoice.maintenance_records.filter(service__isnull=False):
        try:
            services_total += Decimal(str(r.price or 0))
        except Exception:
            services_total += Decimal(r.price or 0)

    # Normalize invoice amount to avoid double-counting
    invoice.amount = services_total + parts_total
    try:
        invoice.save()
    except Exception:
        # ignore save errors during display
        pass

    return render(
        request,
        "pay_invoice.html",
        {
            "form": form,
            "car": car,
            "invoice": invoice,
            "maintenance_date": maintenance_date,
            "invoice_parts": invoice_parts,
            "parts_total": parts_total,
            "service_records": invoice.maintenance_records.filter(service__isnull=False),
        },
    )


@login_required
def pay_invoice(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    invoice = Invoice.objects.filter(car=car, paid=False).first()
    if not invoice:
        return redirect(reverse("cars_list"))

    maintenance_date = (
        MaintenanceRecord.objects.filter(invoice=invoice)
        .order_by("created_at")
        .values_list("created_at", flat=True)
        .first()
    )

    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment_date = form.cleaned_data["payment_date"]
            if isinstance(payment_date, datetime):
                payment_datetime = payment_date
            else:
                payment_datetime = datetime.combine(payment_date, time(12, 0))
            method = form.cleaned_data["method"]
            reference = form.cleaned_data["reference"]
            notes = form.cleaned_data["notes"]
            if method == "benefit" and not reference:
                last_payment = (
                    Payment.objects.filter(method="benefit").order_by("-id").first()
                )
                if last_payment and last_payment.reference and last_payment.reference.isdigit():
                    next_ref = str(int(last_payment.reference) + 1).zfill(7)
                else:
                    next_ref = "0000001"
                reference = next_ref
            Payment.objects.create(
                invoice=invoice,
                car=car,
                client=car.client,
                amount=invoice.amount,
                status="paid",
                payment_date=payment_datetime,
                method=method,
                notes=notes,
                reference=reference,
            )
            invoice.paid = True
            invoice.save()
            car.status = "sold"
            car.save()
            MaintenanceRecord.objects.filter(car=car, is_finished=False).update(
                is_finished=True, ready_at=None
            )
            paid_amount = (
                invoice.payments.filter(status="paid").aggregate(total=models.Sum("amount"))["total"]
                or 0
            )
            remaining_balance = invoice.amount - paid_amount
            # use module-level Decimal import
            invoice_parts = []
            parts_total = Decimal('0.00')
            for r in invoice.maintenance_records.all():
                for p in r.parts.all():
                    invoice_parts.append(p)
                    try:
                        parts_total += Decimal(str(p.total_price or 0))
                    except Exception:
                        parts_total += p.total_price or 0

            return render(
                request,
                "payment_success.html",
                {
                    "car": car,
                    "invoice": invoice,
                    "paid_amount": paid_amount,
                    "remaining_balance": remaining_balance,
                    "invoice_parts": invoice_parts,
                    "parts_total": parts_total,
                    "service_records": invoice.maintenance_records.filter(service__isnull=False),
                    "service_records": invoice.maintenance_records.filter(service__isnull=False),
                },
            )
    else:
        initial = {}
        if request.GET.get("method") == "benefit":
            last_payment = (
                Payment.objects.filter(method="benefit").order_by("-id").first()
            )
            if last_payment and last_payment.reference and last_payment.reference.isdigit():
                next_ref = str(int(last_payment.reference) + 1).zfill(7)
            else:
                next_ref = "0000001"
            initial["reference"] = next_ref
        form = PaymentForm(initial=initial)
    # collect parts and service records for display on the payment page
    invoice_parts = []
    parts_total = Decimal('0.00')
    for r in invoice.maintenance_records.all():
        for p in r.parts.all():
            invoice_parts.append(p)
            try:
                parts_total += Decimal(str(p.total_price or 0))
            except Exception:
                parts_total += Decimal(p.total_price or 0)

    service_records = invoice.maintenance_records.filter(service__isnull=False)

    return render(
        request,
        "pay_invoice.html",
        {
            "form": form,
            "car": car,
            "invoice": invoice,
            "maintenance_date": maintenance_date,
            "invoice_parts": invoice_parts,
            "parts_total": parts_total,
            "service_records": service_records,
        },
    )


@login_required
def payments_list(request):
    payments = Payment.objects.filter(status="paid").select_related("client", "car", "invoice")
    client_id = request.GET.get("client")
    invoice_id = request.GET.get("invoice")
    if client_id:
        payments = payments.filter(client__id=client_id)
    if invoice_id:
        payments = payments.filter(invoice__id=invoice_id)
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    if start_date:
        payments = payments.filter(payment_date__date__gte=parse_date(start_date))
    if end_date:
        payments = payments.filter(payment_date__date__lte=parse_date(end_date))
    payments = payments.order_by("invoice__invoice_number")
    total_amount = payments.aggregate(total=models.Sum("amount"))["total"] or 0
    # Resolve display names for filters
    filter_client_name = None
    filter_invoice_number = None
    if client_id:
        try:
            client_obj = Client.objects.get(id=client_id)
            filter_client_name = f"{client_obj.first_name} {client_obj.last_name or ''}".strip()
        except Client.DoesNotExist:
            filter_client_name = None
    if invoice_id:
        try:
            inv = Invoice.objects.get(id=invoice_id)
            filter_invoice_number = inv.invoice_number
        except Invoice.DoesNotExist:
            filter_invoice_number = None

    return render(
        request,
        "payments_list.html",
        {
            "payments": payments,
            "start_date": start_date,
            "end_date": end_date,
            "total_amount": total_amount,
            "filter_client_id": client_id,
            "filter_invoice_id": invoice_id,
            "filter_client_name": filter_client_name,
            "filter_invoice_number": filter_invoice_number,
        },
    )


@login_required
def invoices_due_list(request):
    invoices = Invoice.objects.filter(paid=False).select_related("client", "car")
    return render(request, "invoices_due_list.html", {"invoices": invoices})


@login_required
def edit_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    if request.method == "POST":
        new_date = request.POST.get("payment_date")
        if new_date:
            payment.payment_date = new_date
            payment.save()
            return redirect("payments_list")
    return render(request, "edit_payment.html", {"payment": payment})


@login_required
def delete_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    if request.method == "POST":
        invoice = payment.invoice
        try:
            payment.delete()
        except Exception:
            messages.error(request, "حدث خطأ أثناء حذف الدفع.")
            return redirect("payments_list")
        # Recompute invoice.paid: if no paid payments remain, mark unpaid
        if invoice:
            paid_exists = invoice.payments.filter(status="paid").exists()
            invoice.paid = True if paid_exists else False
            invoice.save()
        messages.success(request, "تم حذف الدفع بنجاح.")
        return redirect("payments_list")
    return render(request, "delete_payment.html", {"payment": payment})
