from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib import messages

from .models import Car
from .maintenance_models import MaintenanceRecord
from .forms_maintenance import MaintenanceRecordForm
from .forms_edit_maintenance import EditMaintenanceRecordForm

from clients.models import Client
from bookings.models import Booking
from invoices.models import Invoice


@require_GET
def bookings_clients(request):
    # عرض كل الحجوزات الفعلية (status='pending')
    bookings = (
        Booking.objects.select_related("car").filter(status="pending").order_by(
            "-service_date"
        )
    )

    bookings_count = len(bookings)
    html = render_to_string(
        "bookings_clients_list.html",
        {"bookings": bookings, "bookings_count": bookings_count},
    )

    return HttpResponse(html)


# Endpoint لإرجاع عدد السيارات المنتهية (sold)
def get_done_count(request):
    count = Car.objects.filter(status="sold").count()
    return JsonResponse({"done_count": count})


# تعديل سجل الصيانة (حقول منفصلة)
def edit_maintenance_record_fields(request, record_id):
    record = get_object_or_404(MaintenanceRecord, id=record_id)
    if request.method == "POST":
        form = EditMaintenanceRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, "تم تعديل سجل الصيانة بنجاح.")
            return redirect("cars:maintenance_list")
    else:
        form = EditMaintenanceRecordForm(instance=record)
    return render(
        request, "edit_maintenance_record_fields.html", {"form": form, "record": record}
    )


def get_work_duration_dates(car):
    """احسب تاريخ البداية والنهاية للعمل الفعلي للسيارة."""
    maintenance_records = list(car.maintenance_records.all().order_by("created_at"))
    if not maintenance_records:
        return None, None
    start = maintenance_records[0].created_at
    # إذا هناك فاتورة مدفوعة، استخدم تاريخ الدفع
    paid_invoices = car.invoices.filter(paid=True).order_by("-created_at")
    if paid_invoices.exists():
        last_paid = paid_invoices.first()
        last_payment = (
            last_paid.payments.filter(status="paid").order_by("-payment_date").first()
        )
        if last_payment:
            end = last_payment.payment_date
            return start, end
    # إذا لا يوجد فاتورة مدفوعة، استخدم آخر صيانة منتهية
    finished_records = [r for r in maintenance_records if r.is_finished]
    if finished_records:
        end = finished_records[-1].created_at
        return start, end
    # إذا لا يوجد شيء، احسب حتى الآن
    return start, timezone.now()


def get_work_duration_days(car):
    """احسب مدة العمل بالأيام."""
    maintenance_records = list(car.maintenance_records.all().order_by("created_at"))
    if not maintenance_records:
        return None
    start = maintenance_records[0].created_at
    paid_invoices = car.invoices.filter(paid=True).order_by("-created_at")
    if paid_invoices.exists():
        last_paid = paid_invoices.first()
        last_payment = (
            last_paid.payments.filter(status="paid").order_by("-payment_date").first()
        )
        if last_payment:
            end = last_payment.payment_date
            days = (end.date() - start.date()).days + 1
            if days < 0:
                return None
            return days
    finished_records = [r for r in maintenance_records if r.is_finished]
    if finished_records:
        end = finished_records[-1].created_at
        days = (end.date() - start.date()).days + 1
        if days < 0:
            return None
        return days
    end = timezone.now()
    days = (end.date() - start.date()).days + 1
    if days < 0:
        return None
    return days


def cars_ajax_filter(request):
    status = request.GET.get("status")
    status_map = {
        "in_progress": "active",
        "done": "sold",
        "follow": None,  # يمكن تخصيصها لاحقاً
        "pending_payment": "pending_payment",
        "ready": "ready",
    }
    db_status = status_map.get(status)
    if status == "waiting":
        Car.objects.filter(status="waiting").update(status="active")
        cars = Car.objects.filter(status="active").order_by("-created_at")
        cars = [car for car in cars if car.maintenance_records.count() == 0]
    elif status == "in_progress":
        cars = (
            Car.objects.filter(status="active", maintenance_records__is_finished=False)
            .distinct()
            .order_by("-created_at")
        )
    elif status == "done":
        cars = Car.objects.filter(status="sold").order_by("-created_at")[:6]
    elif status == "pending_payment":
        cars = Car.objects.filter(status="pending_payment").order_by("-created_at")
    elif status == "ready":
        cars = Car.objects.filter(status="ready").order_by("-created_at")
    elif db_status:
        cars = Car.objects.filter(status=db_status).order_by("-created_at")
    elif status == "follow":
        cars = Car.objects.none()
    else:
        cars = Car.objects.none()

    cars = list(cars)
    for car in cars:
        start, end = get_work_duration_dates(car)
        car.work_start = start
        car.work_end = end
        car.work_days = get_work_duration_days(car)

    existing_phones = set(Client.objects.values_list("phone_number", flat=True))
    bookings_per_phone = {}
    for phone in existing_phones:
        bookings_per_phone[phone] = list(
            Booking.objects.filter(phone=phone).order_by("-service_date")
        )

    html = render_to_string(
        "cars_list_partial.html",
        {
            "cars": cars,
            "existing_phones": existing_phones,
            "bookings_per_phone": bookings_per_phone,
        },
    )
    return HttpResponse(html)


@login_required
def cars_list(request):
    plate_number = request.GET.get("plate_number")
    status = request.GET.get("status")
    cars = Car.objects.all()
    if status:
        cars = cars.filter(status=status)
    if plate_number:
        cars = cars.filter(plate_number__icontains=plate_number)
    cars = list(cars.order_by("-created_at"))
    return render(request, "cars_list.html", {"cars": cars})


@login_required
def maintenance_list(request):
    plate_number = request.GET.get("plate_number", "").strip()
    qs = MaintenanceRecord.objects.select_related("car", "service", "invoice").order_by(
        "invoice__id"
    )
    if plate_number:
        qs = qs.filter(car__plate_number__icontains=plate_number)
    records = qs
    return render(
        request,
        "maintenance_list.html",
        {"records": records, "plate_number": plate_number},
    )


def edit_maintenance_record(request, record_id):
    record = get_object_or_404(MaintenanceRecord, id=record_id)
    if request.method == "POST":
        form = MaintenanceRecordForm(request.POST)
        if form.is_valid():
            record.service = form.cleaned_data["service"]
            record.price = form.cleaned_data["price"]
            record.notes = form.cleaned_data["notes"]
            record.save()
            return redirect("maintenance_list")
    else:
        form = MaintenanceRecordForm(
            initial={
                "service": record.service,
                "price": record.price,
                "notes": record.notes,
            }
        )
    return render(
        request, "edit_maintenance_record.html", {"form": form, "record": record}
    )


def delete_maintenance_record(request, record_id):
    record = get_object_or_404(MaintenanceRecord, id=record_id)
    if request.method == "POST":
        car = record.car
        record.delete()
        if not car.maintenance_records.exists():
            car.status = "active"
            car.save()
        return redirect("cars:maintenance_list")
    return render(request, "delete_maintenance_record.html", {"record": record})


@require_POST
def finish_maintenance(request, car_id):
    car = get_object_or_404(Car, id=car_id)

    # Mark all maintenance records as finished for this car
    MaintenanceRecord.objects.filter(car=car, is_finished=False).update(
        is_finished=True, ready_at=None
    )
    # Check if all maintenance records are finished
    all_finished = not car.maintenance_records.filter(is_finished=False).exists()
    if car.status == "active" and all_finished:
        car.status = "ready"
        car.save()
        if not car.invoices.filter(paid=False).exists():
            invoice_number = f"INV-{car.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            amount = 0
            for rec in car.maintenance_records.filter(invoice__isnull=True):
                amount += rec.price
            invoice = Invoice.objects.create(
                invoice_number=invoice_number,
                client=car.client,
                car=car,
                amount=amount,
                paid=False,
            )
            for rec in car.maintenance_records.filter(invoice__isnull=True):
                rec.invoice = invoice
                rec.save()
    elif car.status == "active":
        car.status = "active"
        car.save()
    return redirect(f"/cars/?plate_number={car.plate_number}")


@require_POST
def deliver_car(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    if car.status == "ready":
        car.status = "pending_payment"
        car.save()
        unpaid_invoice = car.invoices.filter(paid=False).first()
        if unpaid_invoice is None:
            invoice_number = f"INV-{car.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            amount = 0
            for rec in car.maintenance_records.filter(invoice__isnull=True):
                amount += rec.price
            invoice = Invoice.objects.create(
                invoice_number=invoice_number,
                client=car.client,
                car=car,
                amount=amount,
                paid=False,
            )
            for rec in car.maintenance_records.filter(invoice__isnull=True):
                rec.invoice = invoice
                rec.save()
            unpaid_invoice = invoice
        record_to_deliver = (
            MaintenanceRecord.objects.filter(car=car, delivery_date__isnull=True)
            .order_by("-created_at")
            .first()
        )
        if record_to_deliver:
            record_to_deliver.delivery_date = timezone.now()
            record_to_deliver.save()
    return redirect("/dashboard/")


@require_POST
def start_maintenance(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    if car.status == "waiting":
        car.status = "active"
        car.save()
    return redirect("/cars/?status=active")
