from django.shortcuts import render
from services.models import Service
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from services.forms_service import ServiceFormNoCar


@login_required
def services_add(request):
    if request.method == 'POST':
        form = ServiceFormNoCar(request.POST)
        if form.is_valid():
            form.save()
            return redirect('services_list')
    else:
        form = ServiceFormNoCar()
    return render(request, 'services_add.html', {'form': form})


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
