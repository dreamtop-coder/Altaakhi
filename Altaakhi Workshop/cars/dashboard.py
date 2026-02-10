from django.shortcuts import render
from cars.models import Car


def cars_dashboard(request):
    # حساب عدد السيارات لكل حالة
    counts = {
        "waiting": Car.objects.filter(status="waiting").count(),
        "in_progress": Car.objects.filter(status="active").count(),
        "done": Car.objects.filter(status="sold").count(),
        "follow": 0,  # يمكن تخصيصها لاحقاً
        "pending_payment": Car.objects.filter(status="pending_payment").count(),
        "bookings": 0,  # عداد الحجوزات إذا أردت ربطه فعلياً
    }
    return render(request, "cars_dashboard.html", {"counts": counts})
