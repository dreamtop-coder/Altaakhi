from django.shortcuts import render
from services.models import Service
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from services.forms_service import ServiceFormNoCar
from django.http import JsonResponse
from inventory.models import Part


def services_autocomplete(request):
    q = request.GET.get("q", "").strip()
    results = []
    if q:
        qs = Service.objects.filter(name__icontains=q).order_by('name')[:30]
        results = [{"id": s.id, "name": s.name, "default_price": float(s.default_price or 0)} for s in qs]
    return JsonResponse(results, safe=False)


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


@login_required
def services_parts(request, service_id):
    """Return JSON list of parts associated with a service."""
    try:
        service = Service.objects.get(pk=service_id)
    except Service.DoesNotExist:
        return JsonResponse([], safe=False)
    parts = service.parts.all().order_by('name')
    results = [ {"id": p.id, "name": p.name, "quantity": p.quantity, "purchase_price": float(p.purchase_price), "sale_price": float(p.sale_price)} for p in parts ]
    return JsonResponse(results, safe=False)
