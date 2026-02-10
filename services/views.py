from django.shortcuts import render
from services.models import Service
from django.contrib.auth.decorators import login_required


@login_required
def services_list(request):
    # TEMP: Show all services for debugging
    from django.conf import settings

    services = Service.objects.all()
    print("--- DEBUG ---")
    print("Database path:", settings.DATABASES["default"]["NAME"])
    print("عدد الخدمات في الجدول:", services.count())
    for s in services:
        print("خدمة:", s.name, "| القسم:", s.department, "| السيارة:", s.car)
    print("--- END DEBUG ---")
    return render(request, "services_list.html", {"services": services})
