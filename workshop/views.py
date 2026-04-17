from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

# AJAX: إرجاع بيانات الإيرادات الشهرية لفترة محددة
from django.views.decorators.http import require_GET
@require_GET
def revenue_monthly_ajax(request):
    """
    إرجاع بيانات الإيرادات الشهرية (labels, data) لفترة محددة (من/إلى) بصيغة JSON
    المدخلات: ?from=2025-02&to=2026-01
    """
    from invoices.models import Payment
    from django.db.models.functions import TruncMonth
    from django.db.models import Sum
    from datetime import datetime, timedelta
    from calendar import monthrange
    from django.utils import timezone
    from_str = request.GET.get('from')
    to_str = request.GET.get('to')
    try:
        from_naive = datetime.strptime(from_str, '%Y-%m')
        to_naive = datetime.strptime(to_str, '%Y-%m')
    except Exception:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    # بناء قائمة الأشهر بين from_date و to_date (منسقة كسلاسل 'YYYY-MM')
    months = []
    cur = from_naive
    while cur <= to_naive:
        months.append(cur.strftime('%Y-%m'))
        year = cur.year + (cur.month // 12)
        month = (cur.month % 12) + 1
        cur = cur.replace(year=year, month=month, day=1)
    # حول التواريخ إلى كائنات timezone-aware قبل استخدامهما في الاستعلام
    tz = timezone.get_current_timezone()
    from_date = timezone.make_aware(from_naive.replace(day=1, hour=0, minute=0, second=0, microsecond=0), tz)
    last_day = monthrange(to_naive.year, to_naive.month)[1]
    to_date = timezone.make_aware(to_naive.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999), tz)
    # جلب المدفوعات
    qs = Payment.objects.filter(status='paid', payment_date__gte=from_date, payment_date__lte=to_date)
    qs = qs.annotate(month=TruncMonth('payment_date')).values('month').annotate(total=Sum('amount')).order_by('month')
    monthly_revenue = {m: 0 for m in months}
    for row in qs:
        key = row['month'].strftime('%Y-%m')
        monthly_revenue[key] = float(row['total']) if row['total'] else 0
    return JsonResponse({
        'labels': list(monthly_revenue.keys()),
        'data': list(monthly_revenue.values()),
    })
def clients_list(request):
    from clients.models import Client
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
                customer_id=customer_id
            )
            return redirect(f'/clients/{client.id}/')
        else:
            message = "يرجى تعبئة جميع الحقول المطلوبة."
    search = request.GET.get('search', '').strip()
    clients_qs = Client.objects.all()
    if search:
        clients_qs = clients_qs.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(customer_id__icontains=search) |
            Q(phone_number__icontains=search)
        )
    # Return all clients (no pagination) so the template can display the full list
    clients = clients_qs.order_by('id')
    return render(request, "clients_list.html", {"clients": clients, "message": message, "search": search})
from django.shortcuts import render
from cars.models import Car
from clients.models import Client
from services.models import Service
from invoices.models import Payment, Invoice
from inventory.models import Part
from django.utils import timezone
from django.db.models import Q, Sum

from django.contrib.auth.decorators import login_required

@login_required
def dashboard_summary(request):
    from invoices.models import Payment
    clients_count = Client.objects.count()
    cars_count = Car.objects.count()
    # Show only inventory parts total on the dashboard card (Parts count)
    try:
        services_count = Part.objects.count()
    except Exception:
        services_count = Service.objects.count()
    invoices_count = Invoice.objects.count()
    total_revenue = Payment.objects.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0

    from cars.maintenance_models import MaintenanceRecord
    # Derive filter counts from maintenance records (authoritative) to keep the
    # dashboard badges and AJAX filters consistent. We compute derived status
    # per-car using the same logic as `derive_car_status` in `cars.views`.
    try:
        from cars.views import derive_car_status
        cars_all = list(Car.objects.all())
        counts = {'waiting': 0, 'in_progress': 0, 'pending_payment': 0, 'ready': 0, 'done': 0}
        for car in cars_all:
            try:
                st = derive_car_status(car)
            except Exception:
                st = getattr(car, 'status', None)
            if st in counts:
                counts[st] += 1
        cars_waiting_count = counts.get('waiting', 0)
        cars_in_progress_count = counts.get('in_progress', 0)
        # pending_payment counts cars awaiting payment (derived)
        cars_pending_payment_count = counts.get('pending_payment', 0)
        cars_done_count = counts.get('done', 0)
    except Exception:
        # Fallback to previous DB-based heuristics if derive function unavailable
        cars_waiting_qs = Car.objects.filter(status='waiting').exclude(maintenance_records__is_finished=False)
        cars_waiting_count = 0
        for car in cars_waiting_qs:
            if not MaintenanceRecord.objects.filter(car=car, is_finished=False).exists():
                cars_waiting_count += 1
        cars_in_progress_qs = Car.objects.filter(status='in_progress', maintenance_records__is_finished=False).distinct()
        cars_in_progress_count = 0
        for car in cars_in_progress_qs:
            if MaintenanceRecord.objects.filter(car=car, is_finished=False).exists():
                cars_in_progress_count += 1
        cars_pending_payment_count = Invoice.objects.filter(paid=False).values('client').distinct().count()
        cars_done_count = Car.objects.filter(maintenance_records__isnull=False).exclude(maintenance_records__is_finished=False).exclude(invoices__paid=False).distinct().count()

    # "متابعة" و"حجز": صفر مؤقتاً
    cars_follow_count = 0
    cars_reservation_count = 0

    # الإيرادات الشهرية (آخر 12 شهرًا)
    from invoices.models import Payment
    from django.db.models.functions import TruncMonth
    from datetime import datetime, timedelta
    now = datetime.now()
    months = [(now.replace(day=1) - timedelta(days=30*i)).strftime('%Y-%m') for i in range(11, -1, -1)]
    qs = Payment.objects.filter(status='paid', payment_date__gte=now.replace(day=1) - timedelta(days=365))
    qs = qs.annotate(month=TruncMonth('payment_date')).values('month').annotate(total=Sum('amount')).order_by('month')
    monthly_revenue = {m: 0 for m in months}
    for row in qs:
        key = row['month'].strftime('%Y-%m')
        monthly_revenue[key] = float(row['total']) if row['total'] else 0

    from bookings.models import Booking
    bookings_count = Booking.objects.filter(status='pending').count()
    # Build `counts` dict expected by the dashboard template so badges show correctly
    counts = {
        'waiting': cars_waiting_count,
        'in_progress': cars_in_progress_count,
        'done': cars_done_count,
        'paid_waiting_collection': Car.objects.filter(status='paid_waiting_collection').count(),
        'follow': cars_follow_count,
        'pending_payment': cars_pending_payment_count,
        'bookings': bookings_count,
    }

    context = {
        'clients_count': clients_count,
        'cars_count': cars_count,
        'services_count': services_count,
        'invoices_count': invoices_count,
        'total_revenue': total_revenue,
        'cars_waiting_count': cars_waiting_count,
        'cars_in_progress_count': cars_in_progress_count,
        'cars_done_count': cars_done_count,
        'cars_follow_count': cars_follow_count,
        'cars_pending_payment_count': cars_pending_payment_count,
        'cars_reservation_count': cars_reservation_count,
        'counts': counts,
        'monthly_revenue_labels': list(monthly_revenue.keys()),
        'monthly_revenue_data': list(monthly_revenue.values()),
        'bookings_count': bookings_count,
    }
    return render(request, 'dashboard.html', context)
