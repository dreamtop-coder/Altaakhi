from django.shortcuts import render
from cars.models import Car
from django.db.models import Sum


def derive_car_status(car):
    from django.db.models import Sum as DJSum
    last = car.maintenance_records.filter(delivery_date__isnull=True).order_by('-created_at').first()
    if last:
        inv = getattr(last, 'invoice', None)
        remaining = None
        if inv:
            try:
                paid = inv.payments.filter(status='paid').aggregate(total=DJSum('amount'))['total'] or 0
                remaining = float(inv.amount or 0) - float(paid or 0)
            except Exception:
                remaining = None
        if last.is_finished:
            if remaining is None:
                return 'ready'
            if remaining > 0:
                return 'pending_payment'
            return 'ready'
        else:
            return 'in_progress'
    if car.maintenance_records.filter(delivery_date__isnull=False).exists():
        return 'done'
    return 'waiting'


def cars_dashboard(request):
    # Compute counts using MaintenanceRecord-derived statuses (authoritative)
    counts = {'waiting': 0, 'in_progress': 0, 'done': 0, 'follow': 0, 'pending_payment': 0, 'bookings': 0}
    for car in Car.objects.all():
        st = derive_car_status(car)
        if st == 'ready':
            # treat 'ready' as part of 'done' for dashboard summary (ready for pickup)
            counts['done'] += 1
        elif st in counts:
            counts[st] += 1
        else:
            # unknown, count as waiting
            counts['waiting'] += 1

    return render(request, 'cars_dashboard.html', {'counts': counts})
