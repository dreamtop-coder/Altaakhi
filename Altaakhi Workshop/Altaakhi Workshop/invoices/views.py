from django.contrib.auth.decorators import login_required
from django.db import models
from cars.maintenance_models import MaintenanceRecord
from .forms import EditInvoiceForm
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from .models import Invoice, Payment
from cars.models import Car
from django.urls import reverse
from .forms import PaymentForm
from django.utils.dateparse import parse_date


# عرض وتعديل جماعي لسجلات الصيانة المرتبطة بفاتورة


@login_required
def edit_invoice_records(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    records = MaintenanceRecord.objects.filter(invoice=invoice).select_related(
        "service"
    )
    return render(
        request, "edit_invoice_records.html", {"invoice": invoice, "records": records}
    )




# تعديل الفاتورة (المبلغ فقط حالياً)
@login_required
def edit_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.method == "POST":
        form = EditInvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            invoice = form.save(commit=False)
            if not invoice.created_at:
                from django.utils import timezone

                invoice.created_at = timezone.now()
            invoice.save()
            from django.contrib import messages

            messages.success(request, "تم تعديل الفاتورة بنجاح.")
            return redirect("invoices_list")
    else:
        form = EditInvoiceForm(instance=invoice)
    return render(request, "edit_invoice.html", {"form": form, "invoice": invoice})


@login_required
def invoices_list(request):
    from .models import Invoice
    from django.db.models import Sum
    from django.utils.dateparse import parse_date

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




# حذف الفاتورة إذا لم يكن لها سجلات صيانة مرتبطة
@login_required
def delete_invoice(request, invoice_id):
    from cars.maintenance_models import MaintenanceRecord

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
            return render(
                request, "invoice_already_paid.html", {"invoice": invoice, "car": car}
            )
    except Invoice.DoesNotExist:
        from django.contrib import messages

        messages.error(request, "لا توجد فاتورة بهذا الرقم.")
        return redirect("cars:cars_list")
    # جلب تاريخ أول سجل صيانة مرتبط بهذه الفاتورة (إن وجد)
    from cars.maintenance_models import MaintenanceRecord

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
            from datetime import datetime, time

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
                if (
                    last_payment
                    and last_payment.reference
                    and last_payment.reference.isdigit()
                ):
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
            return render(
                request, "payment_success.html", {"car": car, "invoice": invoice}
            )
    else:
        initial = {}
        if request.GET.get("method") == "benefit":
            last_payment = (
                Payment.objects.filter(method="benefit").order_by("-id").first()
            )
            if (
                last_payment
                and last_payment.reference
                and last_payment.reference.isdigit()
            ):
                next_ref = str(int(last_payment.reference) + 1).zfill(7)
            else:
                next_ref = "0000001"
            initial["reference"] = next_ref
        form = PaymentForm(initial=initial)
    return render(
        request,
        "pay_invoice.html",
        {
            "form": form,
            "car": car,
            "invoice": invoice,
            "maintenance_date": maintenance_date,
        },
    )





@login_required
def pay_invoice(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    invoice = Invoice.objects.filter(car=car, paid=False).first()
    if not invoice:
        return redirect(reverse("cars_list"))

    # جلب تاريخ أول سجل صيانة مرتبط بهذه الفاتورة (إن وجد)
    from cars.maintenance_models import MaintenanceRecord

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
            # تحويل التاريخ إلى datetime مع وقت افتراضي 12:00
            from datetime import datetime, time

            if isinstance(payment_date, datetime):
                payment_datetime = payment_date
            else:
                payment_datetime = datetime.combine(payment_date, time(12, 0))
            method = form.cleaned_data["method"]
            reference = form.cleaned_data["reference"]
            notes = form.cleaned_data["notes"]
            # إذا طريقة الدفع بنفت ولم يدخل المستخدم رقم مرجع، نولده تلقائياً
            if method == "benefit" and not reference:
                last_payment = (
                    Payment.objects.filter(method="benefit").order_by("-id").first()
                )
                if (
                    last_payment
                    and last_payment.reference
                    and last_payment.reference.isdigit()
                ):
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
            # تحديث حالة السيارة إلى منتهية بعد الدفع
            car.status = "sold"
            car.save()
            # تعليم جميع سجلات الصيانة كمُنتهية
            from cars.maintenance_models import MaintenanceRecord

            MaintenanceRecord.objects.filter(car=car, is_finished=False).update(
                is_finished=True, ready_at=None
            )
            # بعد الدفع، اعرض صفحة تأكيد مع تفاصيل الفاتورة وزر طباعة
            return render(
                request, "payment_success.html", {"car": car, "invoice": invoice}
            )
    else:
        # توليد رقم مرجع افتراضي في الفورم إذا كانت أول مرة وبنفت
        initial = {}
        if request.GET.get("method") == "benefit":
            last_payment = (
                Payment.objects.filter(method="benefit").order_by("-id").first()
            )
            if (
                last_payment
                and last_payment.reference
                and last_payment.reference.isdigit()
            ):
                next_ref = str(int(last_payment.reference) + 1).zfill(7)
            else:
                next_ref = "0000001"
            initial["reference"] = next_ref
        form = PaymentForm(initial=initial)
    return render(
        request,
        "pay_invoice.html",
        {
            "form": form,
            "car": car,
            "invoice": invoice,
            "maintenance_date": maintenance_date,
        },
    )


@login_required
def payments_list(request):
    payments = Payment.objects.filter(status="paid").select_related(
        "client", "car", "invoice"
    )
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    if start_date:
        payments = payments.filter(payment_date__date__gte=parse_date(start_date))
    if end_date:
        payments = payments.filter(payment_date__date__lte=parse_date(end_date))
    payments = payments.order_by("invoice__invoice_number")
    # Calculate total amount
    total_amount = payments.aggregate(total=models.Sum("amount"))["total"] or 0
    return render(
        request,
        "payments_list.html",
        {
            "payments": payments,
            "start_date": start_date,
            "end_date": end_date,
            "total_amount": total_amount,
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
