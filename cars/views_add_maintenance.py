from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.shortcuts import render, redirect

from .models import Car
from .forms_add_maintenance import AddMaintenanceForm
from .maintenance_models import MaintenanceRecord
from services.models import Service
from invoices.models import Invoice

# صفحة إضافة سجل صيانة لمركبة


# API: جلب بيانات السيارة والعميل بناءً على رقم اللوحة
@require_GET
def get_car_info(request):
    plate_number = request.GET.get("plate_number")
    try:
        car = Car.objects.select_related("client", "brand", "model").get(
            plate_number=plate_number
        )
        client = car.client
        data = {
            "found": True,
            "client": {
                "name": f"{client.first_name} {client.last_name or ''}",
                "personal_id": getattr(client, "personal_id", ""),
                "phone": getattr(client, "phone", ""),
                "email": getattr(client, "email", "-") or "-",
                "address": getattr(client, "address", "-") or "-",
            },
            "car": {
                "brand": car.brand.name if car.brand else "-",
                "model": car.model.name if car.model else "-",
                "year": car.year or "-",
                "status": dict(car.STATUS_CHOICES).get(car.status, car.status),
                "created_at": car.created_at.strftime("%Y-%m-%d"),
            },
        }
    except Car.DoesNotExist:
        data = {"found": False}
    return JsonResponse(data)


# جلب سعر الخدمة تلقائياً
def get_service_price(request):
    service_id = request.GET.get("service_id")
    try:
        service = Service.objects.get(id=service_id)
        return JsonResponse({"price": float(service.default_price)})
    except Service.DoesNotExist:
        return JsonResponse({"price": ""})


def add_maintenance_record(request):
    car_id = request.GET.get("car_id")
    car_instance = None
    initial = {}
    if car_id:
        try:
            car_instance = Car.objects.get(id=car_id)
            initial["plate_number"] = car_instance.plate_number
        except Car.DoesNotExist:
            car_instance = None
    if request.method == "POST":
        form = AddMaintenanceForm(request.POST, initial=initial)
        if form.is_valid():
            car = form.get_car_instance()
            service = form.cleaned_data["service"]
            price = form.cleaned_data["price"]
            notes = form.cleaned_data["notes"]
            maintenance_date = form.cleaned_data["maintenance_date"]
            car.status = "active"
            car.save()
            if not car or not car.client or not service:
                return render(
                    request,
                    "add_maintenance_record.html",
                    {
                        "form": form,
                        "car_instance": car_instance,
                        "error": "تأكد من وجود السيارة والعميل والخدمة بشكل صحيح.",
                    },
                )
            invoice = Invoice.objects.filter(
                car=car, client=car.client, paid=False
            ).first()
            if not invoice:
                last_invoice = Invoice.objects.order_by("-id").first()
                if last_invoice and last_invoice.invoice_number.isdigit():
                    next_number = int(last_invoice.invoice_number) + 1
                else:
                    next_number = 1
                invoice_number = f"{next_number:06d}"
                invoice = Invoice.objects.create(
                    invoice_number=invoice_number,
                    client=car.client,
                    car=car,
                    amount=0,
                    paid=False,
                    created_at=maintenance_date,
                )
            MaintenanceRecord.objects.create(
                car=car,
                service=service,
                price=price,
                notes=notes,
                created_at=maintenance_date,
                invoice=invoice,
            )
            # إذا كانت السيارة في حالة waiting، انقلها إلى active
            if car.status == "waiting":
                car.status = "active"
                car.save()
            if service.pk not in invoice.services.values_list("pk", flat=True):
                invoice.services.add(service.pk)
            total = sum(r.price for r in invoice.maintenance_records.all())
            invoice.amount = total
            invoice.save()
            return redirect("/dashboard/")
    else:
        form = AddMaintenanceForm(initial=initial)
    return render(
        request,
        "add_maintenance_record.html",
        {"form": form, "car_instance": car_instance},
    )
