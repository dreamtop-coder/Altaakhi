from django.views.decorators.http import require_POST
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Booking
from .forms import BookingForm



# تحويل الحجز إلى سجل صيانة
@require_POST
def booking_start_maintenance(request, booking_id):
    from cars.maintenance_models import MaintenanceRecord
    from services.models import Service

    booking = get_object_or_404(Booking, id=booking_id)
    # محاولة جلب الخدمة بناءً على اسمها في الحجز
    service = None
    if booking.service_type:
        try:
            service = Service.objects.get(name=booking.service_type)
        except Service.DoesNotExist:
            service = None
    # إذا كانت السيارة حالتها ليست نشطة، يتم تحويلها إلى نشطة عند بدء الصيانة
    if booking.car and booking.car.status != "active":
        booking.car.status = "active"
        booking.car.save()
    MaintenanceRecord.objects.create(
        car=booking.car,
        service=service,
        price=service.default_price if service else 0,
        notes=booking.notes,
        created_at=timezone.now(),
        is_finished=False,
    )
    booking.delete()
    return redirect("bookings_list")




# AJAX endpoint to get car and client info by plate number
def booking_car_info_ajax(request):
    plate_number = request.GET.get("plate_number")
    if not plate_number:
        return JsonResponse({"error": "رقم السيارة مطلوب."}, status=400)
    from cars.models import Car

    try:
        car = Car.objects.select_related("client", "brand", "model").get(
            plate_number=plate_number
        )
        car_info = {
            "plate_number": car.plate_number,
            "status": car.status,
            "model": car.model.name if car.model else "-",
            "brand": car.brand.name if car.brand else "-",
            "year": car.year,
            "created_at": car.created_at.strftime("%Y-%m-%d")
            if car.created_at
            else "-",
        }
        client = car.client
        if client:
            client_info = {
                "name": f"{client.first_name} {client.last_name if client.last_name else ''}",
                "national_id": getattr(client, "customer_id", "-"),
                "phone": client.phone_number,
                "email": client.email,
                "address": client.address,
            }
        else:
            client_info = None
        return JsonResponse({"car_info": car_info, "client_info": client_info})
    except Car.DoesNotExist:
        return JsonResponse({"error": "لا يوجد سيارة بهذا الرقم."}, status=404)




def bookings_list(request):
    from datetime import date

    bookings = Booking.objects.filter(status="pending").order_by("-service_date")
    today = date.today()
    print("DEBUG: عدد الحجوزات:", bookings.count())
    print("DEBUG: الحجوزات:", list(bookings.values()))
    return render(request, "bookings_list.html", {"bookings": bookings, "today": today})


def booking_create(request):
    client_info = None
    car_info = None
    if request.method == "POST":
        form = BookingForm(request.POST)
        plate_number = request.POST.get("plate_number") or (
            form.cleaned_data.get("plate_number") if form.is_valid() else None
        )
        if plate_number:
            from cars.models import Car

            try:
                car = Car.objects.select_related("client", "brand", "model").get(
                    plate_number=plate_number
                )
                car_info = {
                    "plate_number": car.plate_number,
                    "status": car.status,
                    "model": car.model.name if car.model else "-",
                    "brand": car.brand.name if car.brand else "-",
                    "year": car.year,
                    "created_at": car.created_at,
                }
                client = car.client
                if client:
                    client_info = {
                        "name": f"{client.first_name} {client.last_name if client.last_name else ''}",
                        "national_id": getattr(client, "customer_id", "-"),
                        "phone": client.phone_number,
                        "email": client.email,
                        "address": client.address,
                    }
                else:
                    client_info = None
            except Car.DoesNotExist:
                car_info = None
                client_info = None
        if form.is_valid():
            form.save()
            return redirect("bookings_list")
    else:
        form = BookingForm()
    return render(
        request,
        "booking_form.html",
        {"form": form, "client_info": client_info, "car_info": car_info},
    )


def booking_edit(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == "POST":
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            return redirect("bookings_list")
    else:
        form = BookingForm(instance=booking)
    return render(request, "booking_form.html", {"form": form, "edit": True})


def booking_delete(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == "POST":
        booking.delete()
        return redirect("bookings_list")
    return render(request, "booking_confirm_delete.html", {"booking": booking})
