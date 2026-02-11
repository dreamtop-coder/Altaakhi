from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
import traceback
from .models import Client
from audit.models import AuditLog
from cars.models import Car
from .forms import ClientForm
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden


def clients_list(request):
    print("=== TEST INSIDE FUNCTION ===")
    search = request.GET.get("search", "").strip()
    print(f"[DEBUG] قيمة البحث المستلمة: '{search}'")
    clients_qs = Client.objects.all()
    cars_matched_by_search = {}  # client_id -> list of matched plate_numbers
    if search:
        normalized_search = search.replace(" ", "").upper()
        print(f"[DEBUG] Normalized search: '{normalized_search}'")
        print("[DEBUG] --- جميع أرقام السيارات في قاعدة البيانات بعد التطبيع ---")
        for car in Car.objects.all():
            normalized_plate = (
                car.plate_number.replace(" ", "").upper() if car.plate_number else ""
            )
            print(
                f"[DEBUG] plate_number='{car.plate_number}' | normalized='{normalized_plate}' | len={len(car.plate_number)} | client_id={car.client_id}"
            )
        # البحث في جميع الحقول كما هو
        car_ids = [
            car.client_id
            for car in Car.objects.all()
            if car.plate_number
            and normalized_search in car.plate_number.replace(" ", "").upper()
        ]
        clients_qs = Client.objects.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(customer_id__icontains=search)
            | Q(phone_number__icontains=search)
            | Q(id__in=car_ids)
        ).distinct()
        # تجهيز قائمة أرقام السيارات المطابقة لكل عميل (للاستخدام في القالب)
        for client in clients_qs:
            matched_plates = [
                car.plate_number
                for car in client.cars.all()
                if car.plate_number
                and normalized_search in car.plate_number.replace(" ", "").upper()
            ]
            if matched_plates:
                cars_matched_by_search[client.id] = matched_plates
        print(
            f"[DEBUG] نتائج البحث بعد الفلترة: {clients_qs.count()} | البحث: '{search}' | أرقام السيارات المطابقة بعد التطبيع: {cars_matched_by_search}"
        )
    clients_qs = clients_qs.order_by("-created_at")
    print(f"[DEBUG] عدد العملاء بعد الفلترة: {clients_qs.count()} | البحث: {search}")
    paginator = Paginator(clients_qs, 10)
    page_number = request.GET.get("page")
    if search:
        page_number = 1
    clients = paginator.get_page(page_number)
    return render(
        request,
        "clients_list.html",
        {
            "clients": clients,
            "search": search,
            "cars_matched_by_search": cars_matched_by_search,
        },
    )


def add_client(request):
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            if not client.created_at:
                client.created_at = timezone.now()
            client.save()
            return redirect("client_detail", client_id=client.id)
    else:
        # جلب رقم الهاتف من باراميتر البحث إن وجد
        phone_number = request.GET.get("search", "").strip()
        initial = {"phone_number": phone_number} if phone_number else None
        form = ClientForm(initial=initial)
    return render(request, "clients/add_client.html", {"form": form})


@login_required
def delete_client(request, client_id):
    # Log and forbid unauthorized delete attempts
    if not request.user.has_perm('clients.delete_client'):
        try:
            AuditLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action="DELETE_ATTEMPT_DENIED",
                object_type="Client",
                object_id=str(client_id),
                description=f"User {request.user} attempted to delete client id={client_id} without permission",
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        except Exception:
            pass
        return HttpResponseForbidden()
    client = get_object_or_404(Client, id=client_id)
    # Prevent deleting a client who has paid invoices.
    paid_invoices = client.invoices.filter(paid=True).select_related("car")
    if paid_invoices.exists():
        # If POST was attempted, do not perform deletion; show instructions instead
        return render(
            request,
            "clients/delete_client.html",
            {"client": client, "block_delete": True, "paid_invoices": paid_invoices},
        )

    if request.method == "POST":
        try:
            client.delete()
            try:
                AuditLog.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action="DELETE_CLIENT",
                    object_type="Client",
                    object_id=str(client_id),
                    description=f"Deleted client {client.first_name} {client.last_name or ''} (id={client_id})",
                    ip_address=request.META.get("REMOTE_ADDR"),
                )
            except Exception:
                pass
            return redirect("clients_list")
        except Exception:
            return HttpResponse('<pre>' + traceback.format_exc() + '</pre>')
    return render(request, "clients/delete_client.html", {"client": client})


def client_detail(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    cars = client.cars.all()
    # لكل مركبة: جلب سجلات الصيانة والفواتير
    cars_data = []
    for car in cars:
        maintenance_records = (
            car.maintenance_records.select_related("invoice", "service")
            .all()
            .order_by("-created_at")
        )
        records_with_payments = []
        for record in maintenance_records:
            payment_dates = []
            if record.invoice:
                payments = record.invoice.payments.filter(status="paid").order_by(
                    "payment_date"
                )
                payment_dates = [p.payment_date for p in payments]
            records_with_payments.append(
                {"record": record, "payment_dates": payment_dates}
            )
        # إضافة has_unpaid_invoice لكل مركبة
        has_unpaid_invoice = car.invoices.filter(paid=False).exists()
        cars_data.append(
            {
                "car": car,
                "maintenance_records": records_with_payments,
                "has_unpaid_invoice": has_unpaid_invoice,
            }
        )
    return render(
        request,
        "client_detail.html",
        {
            "client": client,
            "cars_data": cars_data,
        },
    )


def edit_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect("clients_list")
    else:
        form = ClientForm(instance=client)
    return render(request, "clients/edit_client.html", {"form": form, "client": client})
