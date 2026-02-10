from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .forms import CarForm
from clients.models import Client
from .brand_models import CarModel


def add_car_for_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == "POST":
        form = CarForm(request.POST)
        if form.is_valid():
            car = form.save(commit=False)
            car.client = client
            car.save()
            # ربط الحجوزات التي تحمل نفس رقم اللوحة بهذه السيارة
            from bookings.models import Booking

            Booking.objects.filter(
                car__isnull=True, plate_number=car.plate_number
            ).update(car=car)
            return redirect("client_detail", client_id=client.id)
    else:
        form = CarForm()
    return render(request, "add_car_for_client.html", {"form": form, "client": client})


def get_models_for_brand(request):
    brand_id = request.GET.get("brand_id")
    models = CarModel.objects.filter(brand_id=brand_id).order_by("name")
    data = {"models": [{"id": m.id, "name": m.name} for m in models]}
    return JsonResponse(data)
