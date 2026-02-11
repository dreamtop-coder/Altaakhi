from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.http import HttpResponse
import traceback
from decimal import Decimal
from django.utils import timezone
from datetime import datetime

from .models import Car
from .forms_add_maintenance import AddMaintenanceForm
from .maintenance_models import MaintenanceRecord
from .maintenance_models import MaintenancePart
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
                # map to the actual Client model fields: customer_id and phone_number
                "personal_id": getattr(client, "customer_id", ""),
                "phone": getattr(client, "phone_number", ""),
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
    try:
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
            # make a mutable copy of POST so we can inject inferred fields (service, price, maintenance_date)
            post_data = request.POST.copy()
            # ensure maintenance_date exists (default to today) to avoid validation error
            if not post_data.get('maintenance_date'):
                try:
                    from datetime import date

                    post_data['maintenance_date'] = date.today().isoformat()
                except Exception:
                    post_data['maintenance_date'] = ''

            # If the form was opened from a car card (car_id in GET), inject the plate number
            # into POST so bound form validation (required plate field) passes.
            if car_instance and not post_data.get('plate_number'):
                post_data['plate_number'] = car_instance.plate_number

            # try to infer service from submitted service_parts (added by JS) when top service field is empty
            if not post_data.get('service'):
                try:
                    import json

                    parts_json = post_data.get('service_parts')
                    parts_list = json.loads(parts_json) if parts_json else []
                except Exception:
                    parts_list = []
                if parts_list:
                    for it in parts_list:
                        if not it.get('id') and it.get('name'):
                            svc_name = (it.get('name') or '').strip()
                            svc = Service.objects.filter(name__iexact=svc_name).first()
                            # try more flexible matches if exact fails
                            if not svc:
                                svc = Service.objects.filter(name__icontains=svc_name).first()
                            if not svc:
                                svc = Service.objects.filter(name__istartswith=svc_name).first()
                            if svc:
                                post_data['service'] = str(svc.id)
                                # set price from service default
                                try:
                                    post_data['price'] = str(float(getattr(svc, 'default_price', 0) or 0))
                                except Exception:
                                    post_data['price'] = '0'
                                break
                    # if still no service set, but a row contains a unit price, use that as price
                    if not post_data.get('service') and not post_data.get('price'):
                        for it in parts_list:
                            if it.get('unit'):
                                try:
                                    post_data['price'] = str(float(it.get('unit') or 0))
                                    break
                                except Exception:
                                    continue

            form = AddMaintenanceForm(post_data, initial=initial)
            if form.is_valid():
                car = form.get_car_instance()
                service = form.cleaned_data.get("service")
                price = form.cleaned_data.get("price")
                notes = form.cleaned_data["notes"]
                maintenance_date = form.cleaned_data["maintenance_date"]

                # Parse parts early to validate stock first so missing parts
                # produce the specific out-of-stock message instead of the
                # generic "ensure car/client/service" message.
                try:
                    import json
                    from inventory.models import Part as InvPart
                    parts_json = request.POST.get('service_parts')
                    parts_list = json.loads(parts_json) if parts_json else []
                except Exception:
                    parts_list = []

                stock_errors = []
                for item in parts_list:
                    # skip service (labor) rows which are not inventory items
                    if item.get('is_service') or item.get('service_id'):
                        continue
                    try:
                        qty = int(item.get('qty') or 1)
                    except Exception:
                        qty = 1
                    pid = int(item.get('id') or 0)
                    if pid:
                        try:
                            p = InvPart.objects.get(pk=pid)
                            if getattr(p, 'is_stock_item', True) and p.quantity < qty:
                                stock_errors.append("هذا القطعة غير متوفر حاليا")
                        except InvPart.DoesNotExist:
                            stock_errors.append("هذا القطعة غير متوفر حاليا")
                    else:
                        name = (item.get('name') or '').strip()
                        if name:
                            p = InvPart.objects.filter(name__iexact=name).first()
                            if p:
                                if getattr(p, 'is_stock_item', True) and p.quantity < qty:
                                    stock_errors.append("هذا القطعة غير متوفر حاليا")
                            else:
                                stock_errors.append("هذا القطعة غير متوفر حاليا")

                if stock_errors:
                    return render(
                        request,
                        "add_maintenance_record.html",
                        {
                            "form": form,
                            "car_instance": car_instance,
                            "error": "\n".join(stock_errors),
                        },
                    )

                # If service not provided in the top field, try to infer it from invoice rows submitted
                if not service:
                    try:
                        import json
                        parts_json = request.POST.get('service_parts')
                        parts_list = json.loads(parts_json) if parts_json else []
                    except Exception:
                        parts_list = []
                    # look for an item whose id is null and whose name matches a Service
                    if parts_list:
                        for it in parts_list:
                            if not it.get('id') and it.get('name'):
                                svc_name = (it.get('name') or '').strip()
                                svc = Service.objects.filter(name__iexact=svc_name).first()
                                if svc:
                                    service = svc
                                    break

                car.status = "active"
                car.save()

                # Require car and client, but allow service to be empty for
                # parts-only maintenance records (customer buying parts).
                if not car or not car.client:
                    return render(
                        request,
                        "add_maintenance_record.html",
                        {
                            "form": form,
                            "car_instance": car_instance,
                            "error": "تأكد من وجود السيارة والعميل بشكل صحيح.",
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
                # Ensure price is taken from the service definition (price field removed from top form)
                try:
                    if service:
                        price = Decimal(str(getattr(service, 'default_price', 0) or 0))
                except Exception:
                    try:
                        price = Decimal(str(price or 0))
                    except Exception:
                        price = Decimal('0.00')

                # If this is a parts-only record (no service selected or inferred),
                # do not treat any submitted unit price as a service charge —
                # set maintenance price to 0 so invoice only counts part totals.
                if not service:
                    price = Decimal('0.00')

                from django.db.utils import IntegrityError
                try:
                    maintenance = MaintenanceRecord.objects.create(
                        car=car,
                        service=service,
                        price=price,
                        notes=notes,
                        created_at=maintenance_date,
                        invoice=invoice,
                    )
                except IntegrityError:
                    # Likely DB schema still requires a non-null service_id.
                    return render(
                        request,
                        "add_maintenance_record.html",
                        {
                            "form": form,
                            "car_instance": car_instance,
                            "error": "قاعدة البيانات لا تسمح بحقل الخدمة الفارغ. شغّل: manage.py migrate cars ثم أعد المحاولة.",
                        },
                    )
                # handle parts submitted with the maintenance
                import json
                try:
                    parts_json = request.POST.get('service_parts')
                    parts_list = json.loads(parts_json) if parts_json else []
                except Exception:
                    parts_list = []
                parts_total = Decimal('0.00')
                # reload the maintenance record we just created (variable `maintenance` exists)
                if maintenance and parts_list:
                    from inventory.models import Part as InvPart
                    for item in parts_list:
                        # Skip rows that represent services (labor) — they should not
                        # be recorded as inventory parts, otherwise totals double-count.
                        if item.get('is_service') or item.get('service_id'):
                            continue
                        pid = int(item.get('id') or 0)
                        qty = int(item.get('qty') or 1)
                        part_obj = None
                        try:
                            part_obj = InvPart.objects.get(pk=pid)
                        except Exception:
                            part_obj = None
                        if part_obj:
                            unit = Decimal(str(part_obj.sale_price or 0))
                        else:
                            unit = Decimal(str(item.get('unit') or 0))
                        total = unit * Decimal(qty)
                        MaintenancePart.objects.create(
                            maintenance=maintenance,
                            part=part_obj,
                            part_name=(part_obj.name if part_obj else item.get('name') or ''),
                            quantity=qty,
                            unit_price=unit,
                            total_price=total,
                        )
                        parts_total += total
                        # decrement stock for stock items
                        if part_obj and getattr(part_obj, 'is_stock_item', True):
                            part_obj.quantity = max(0, part_obj.quantity - qty)
                            part_obj.save()
                # NOTE: Do not mark maintenance finished automatically here.
                # The maintenance record is created and left in-progress (is_finished=False)
                # so the normal workflow (finish -> ready -> deliver -> pending_payment) is preserved.
                # maintenance.save() remains the record of creation above.

                # add parts total to invoice amount (we'll recompute full invoice below)
                if parts_total:
                    # ensure invoice.amount is Decimal before adding
                    try:
                        invoice.amount = (Decimal(str(invoice.amount)) if not isinstance(invoice.amount, Decimal) else invoice.amount) + parts_total
                    except Exception:
                        invoice.amount = Decimal(str(invoice.amount)) + parts_total
                    invoice.save()
                # إذا كانت السيارة في حالة waiting، انقلها إلى active
                if car.status == "waiting":
                    car.status = "active"
                    car.save()
                if service and service.pk not in invoice.services.values_list("pk", flat=True):
                    invoice.services.add(service.pk)
                # Recompute invoice amount as sum of service prices + parts used in those maintenance records
                services_total = sum(
                    (r.price or Decimal("0.00"))
                    for r in invoice.maintenance_records.all()
                )

                parts_sum = Decimal("0.00")

                for r in invoice.maintenance_records.all():
                    parts_sum += sum(
                        (Decimal(str(p.total_price or 0)))
                        for p in r.parts.all()
                    )

                invoice.amount = services_total + parts_sum
                invoice.save()
                return redirect(f"/cars/?plate_number={car.plate_number}")
        else:
            form = AddMaintenanceForm(initial=initial)
    except Exception:
        return HttpResponse('<pre>' + traceback.format_exc() + '</pre>')
    # compute next invoice number for display
    last_invoice = Invoice.objects.order_by("-id").first()
    if last_invoice and getattr(last_invoice, 'invoice_number', '').isdigit():
        try:
            next_number = int(last_invoice.invoice_number) + 1
        except Exception:
            next_number = 1
    else:
        next_number = 1
    next_invoice_number = f"{next_number:06d}"

    return render(
        request,
        "add_maintenance_record.html",
        {"form": form, "car_instance": car_instance, "next_invoice_number": next_invoice_number},
    )
