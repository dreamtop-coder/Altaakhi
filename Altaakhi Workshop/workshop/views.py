from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import render, redirect
from django.db.models import Q, Sum
from django.db.models.functions import TruncMonth
from django.utils.dateparse import parse_date
from datetime import datetime, timedelta, time
from calendar import monthrange
from invoices.models import Payment, Invoice
from cars.models import Car
from clients.models import Client
from services.models import Service
from bookings.models import Booking
from cars.maintenance_models import MaintenanceRecord


@require_GET
def revenue_monthly_ajax(request):
    """
    إرجاع بيانات الإيرادات الشهرية (labels, data) لفترة محددة (من/إلى) بصيغة JSON
    المدخلات: ?from=2025-02&to=2026-01
    """
    # uses `Payment`, `TruncMonth`, `datetime`, `monthrange` from module imports

    from_str = request.GET.get("from")
    to_str = request.GET.get("to")
    try:
        from_date = datetime.strptime(from_str, "%Y-%m")
        to_date = datetime.strptime(to_str, "%Y-%m")
    except Exception:
        return JsonResponse({"error": "Invalid date format"}, status=400)
    # بناء قائمة الأشهر بين from_date و to_date
    months = []
    cur = from_date
    while cur <= to_date:
        months.append(cur.strftime("%Y-%m"))
        # الانتقال للشهر التالي
        year = cur.year + (cur.month // 12)
        month = (cur.month % 12) + 1
        cur = cur.replace(year=year, month=month, day=1)
    # جلب المدفوعات
    qs = Payment.objects.filter(
        status="paid",
        payment_date__gte=from_date,
        payment_date__lte=to_date.replace(
            day=monthrange(to_date.year, to_date.month)[1]
        ),
    )
    qs = (
        qs.annotate(month=TruncMonth("payment_date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )
    monthly_revenue = {m: 0 for m in months}
    for row in qs:
        key = row["month"].strftime("%Y-%m")
        monthly_revenue[key] = float(row["total"]) if row["total"] else 0
    return JsonResponse(
        {
            "labels": list(monthly_revenue.keys()),
            "data": list(monthly_revenue.values()),
        }
    )


def clients_list(request):
    message = None
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()
        email = request.POST.get("email", "").strip()
        address = request.POST.get("address", "").strip()
        customer_id = request.POST.get("customer_id", "").strip()
        if first_name and last_name and phone_number and customer_id:
            client = Client.objects.create(
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                email=email,
                address=address,
                customer_id=customer_id,
            )
            return redirect(f"/clients/{client.id}/")
        else:
            message = "يرجى تعبئة جميع الحقول المطلوبة."
    search = request.GET.get("search", "").strip()
    clients_qs = Client.objects.all()
    if search:
        clients_qs = clients_qs.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(customer_id__icontains=search)
            | Q(phone_number__icontains=search)
        )
    clients = clients_qs.order_by("-created_at")[:10]
    return render(
        request,
        "clients_list.html",
        {"clients": clients, "message": message, "search": search},
    )


    
@login_required
def dashboard_summary(request):
    from invoices.models import Payment
    clients_count = Client.objects.count()
    cars_count = Car.objects.count()
    services_count = Service.objects.count()
    invoices_count = Invoice.objects.count()
    total_revenue = (
        Payment.objects.filter(status="paid").aggregate(total=Sum("amount"))["total"]
        or 0
    )

    # "قيد الانتظار": سيارات active ليس لها أي سجل صيانة نشط (أي لا يوجد MaintenanceRecord غير منتهية)
    cars_waiting_qs = Car.objects.filter(status="active").exclude(
        maintenance_records__is_finished=False
    )
    cars_waiting_count = 0
    for car in cars_waiting_qs:
        if not MaintenanceRecord.objects.filter(car=car, is_finished=False).exists():
            cars_waiting_count += 1

    # "جاري التنفيذ": سيارات active لديها سجل صيانة نشط فعلاً (is_finished=False)
    cars_in_progress_qs = Car.objects.filter(
        status="active", maintenance_records__is_finished=False
    ).distinct()
    cars_in_progress_count = 0
    for car in cars_in_progress_qs:
        if MaintenanceRecord.objects.filter(car=car, is_finished=False).exists():
            cars_in_progress_count += 1

    # "معلقة للدفع": سيارات لديها فاتورة غير مدفوعة
    cars_pending_payment_count = (
        Car.objects.filter(invoices__paid=False, invoices__isnull=False)
        .distinct()
        .count()
    )

    # "منتهية": سيارات لها سجل صيانة واحد على الأقل، ولا يوجد لها أي صيانة نشطة ولا أي فاتورة غير مدفوعة
    cars_done_count = (
        Car.objects.filter(maintenance_records__isnull=False)
        .exclude(maintenance_records__is_finished=False)
        .exclude(invoices__paid=False)
        .distinct()
        .count()
    )

    # "متابعة" و"حجز": صفر مؤقتاً
    cars_follow_count = 0
    cars_reservation_count = 0

    # الإيرادات الشهرية (آخر 12 شهرًا)
    # uses `Payment`, `TruncMonth`, `datetime`, `timedelta` from module imports
    now = datetime.now()
    months = [
        (now.replace(day=1) - timedelta(days=30 * i)).strftime("%Y-%m")
        for i in range(11, -1, -1)
    ]
    qs = Payment.objects.filter(
        status="paid", payment_date__gte=now.replace(day=1) - timedelta(days=365)
    )
    qs = (
        qs.annotate(month=TruncMonth("payment_date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )
    monthly_revenue = {m: 0 for m in months}
    for row in qs:
        key = row["month"].strftime("%Y-%m")
        monthly_revenue[key] = float(row["total"]) if row["total"] else 0

    # Booking imported at module top

    bookings_count = Booking.objects.filter(status="pending").count()
    context = {
        "clients_count": clients_count,
        "cars_count": cars_count,
        "services_count": services_count,
        "invoices_count": invoices_count,
        "total_revenue": total_revenue,
        "cars_waiting_count": cars_waiting_count,
        "cars_in_progress_count": cars_in_progress_count,
        "cars_done_count": cars_done_count,
        "cars_follow_count": cars_follow_count,
        "cars_pending_payment_count": cars_pending_payment_count,
        "cars_reservation_count": cars_reservation_count,
        "monthly_revenue_labels": list(monthly_revenue.keys()),
        "monthly_revenue_data": list(monthly_revenue.values()),
        "bookings_count": bookings_count,
    }
    return render(request, "dashboard.html", context)
