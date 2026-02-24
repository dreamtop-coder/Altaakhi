from django.views.decorators.http import require_GET
from django.db.models import Q

# API: جلب بيانات السيارة والعميل بناءً على رقم اللوحة
@require_GET
def get_car_info(request):
    plate_number = request.GET.get('plate_number')
    from .models import Car
    try:
        car = Car.objects.select_related('client', 'brand', 'model').get(plate_number=plate_number)
        client = car.client
        data = {
            'found': True,
            'client': {
                'name': f"{client.first_name} {client.last_name or ''}",
                'personal_id': getattr(client, 'personal_id', ''),
                'phone': getattr(client, 'phone', ''),
                'email': getattr(client, 'email', '-') or '-',
                'address': getattr(client, 'address', '-') or '-',
            },
            'car': {
                'brand': car.brand.name if car.brand else '-',
                'model': car.model.name if car.model else '-',
                'year': car.year or '-',
                'status': dict(car.STATUS_CHOICES).get(car.status, car.status),
                'created_at': car.created_at.strftime('%Y-%m-%d'),
            }
        }
    except Car.DoesNotExist:
        data = {'found': False}
    return JsonResponse(data)
# جلب سعر الخدمة تلقائياً
from django.http import JsonResponse
from services.models import Service

def get_service_price(request):
    service_id = request.GET.get('service_id')
    try:
        service = Service.objects.get(id=service_id)
        return JsonResponse({'price': float(service.default_price)})
    except Service.DoesNotExist:
        return JsonResponse({'price': ''})
from django.shortcuts import render, redirect
from .forms_add_maintenance import AddMaintenanceForm

from .maintenance_models import MaintenanceRecord
from invoices.models import Invoice

# صفحة إضافة سجل صيانة لمركبة

def add_maintenance_record(request):
    from .models import Car
    car_id = request.GET.get('car_id')
    car_instance = None
    initial = {}
    if car_id:
        try:
            car_instance = Car.objects.get(id=car_id)
            initial['plate_number'] = car_instance.plate_number
        except Car.DoesNotExist:
            car_instance = None
    # Prefill maintenance/invoice date with today's date (editable)
    try:
        from django.utils import timezone
        today = timezone.now().date()
        # date input expects YYYY-MM-DD
        initial['maintenance_date'] = today.strftime('%Y-%m-%d')
    except Exception:
        pass
    if request.method == 'POST':
        # Early debug: record that a POST was received and list top-level keys
        try:
            with open('debug_received_post.log', 'a', encoding='utf-8') as _f:
                _f.write(f"RECEIVED POST: keys={list(request.POST.keys())}\n")
        except Exception:
            pass
        # If user selected a client earlier in the form (selected_client_id),
        # prepare the `selected_client_car` queryset before validating the form
        sel_cid = request.POST.get('selected_client_id')
        client_for_queryset = None
        if sel_cid:
            try:
                from clients.models import Client
                client_for_queryset = Client.objects.get(id=sel_cid)
            except Exception:
                client_for_queryset = None

        form = AddMaintenanceForm(request.POST, initial=initial)
        try:
            if client_for_queryset:
                form.fields['selected_client_car'].queryset = Car.objects.filter(client=client_for_queryset)
        except Exception:
            pass

        if form.is_valid():
            car = form.get_car_instance()
            # Fallback: if form did not resolve a car instance, try to find by plate number
            if not car:
                plate = (request.POST.get('plate_number') or form.cleaned_data.get('plate_number') or initial.get('plate_number'))
                if plate:
                    try:
                        car = Car.objects.filter(plate_number__iexact=plate).first()
                    except Exception:
                        car = None
            service = form.cleaned_data.get('service')
            price = form.cleaned_data.get('price')
            notes = form.cleaned_data['notes']
            maintenance_date = form.cleaned_data['maintenance_date']
            # ensure car exists before changing status (we'll update status after creating records)
            if car:
                try:
                    try:
                        with open('debug_car_status.log', 'a', encoding='utf-8') as _f:
                            _f.write(f"BEFORE: car_id={car.id} status={getattr(car,'status',None)}\n")
                    except Exception:
                        pass
                except Exception:
                    pass
            # NOTE: do not prematurely block if client is provided via selected_client_id
            # determine client: from car if present, otherwise from selected_client_id
            client_obj = None
            if car:
                client_obj = getattr(car, 'client', None)
            else:
                sel_cid = request.POST.get('selected_client_id')
                if sel_cid:
                    try:
                        from clients.models import Client
                        client_obj = Client.objects.get(id=sel_cid)
                    except Exception:
                        client_obj = None

            # If car wasn't resolved earlier, attempt to resolve from submitted plate
            if not car:
                try:
                    plate_sub = (request.POST.get('plate_number') or '').strip()
                    if plate_sub:
                        car = Car.objects.filter(plate_number__iexact=plate_sub).first()
                except Exception:
                    car = None

            # If still no car but we have a client, try to resolve heuristically.
            if not car and client_obj:
                try:
                    client_cars_qs = Car.objects.filter(client=client_obj)
                    cnt = client_cars_qs.count()
                    if cnt == 1:
                        car = client_cars_qs.first()
                    elif cnt > 1:
                        # If client has multiple cars and the user didn't explicitly
                        # select one via the `selected_client_car` field or plate,
                        # require explicit selection to avoid guessing.
                        sel_car_from_form = form.cleaned_data.get('selected_client_car') if hasattr(form, 'cleaned_data') else None
                        plate_sub2 = (request.POST.get('plate_number') or '').strip()
                        if not sel_car_from_form and not plate_sub2:
                            return render(request, 'add_maintenance_record.html', {
                                'form': form,
                                'car_instance': car_instance,
                                'clients_sample': [],
                                'error': 'العميل لديه أكثر من مركبة، الرجاء اختيار رقم اللوحة أو تحديد المركبة من القائمة.'
                            })
                except Exception:
                    pass

            if not client_obj:
                return render(request, 'add_maintenance_record.html', {'form': form, 'car_instance': car_instance, 'error': 'تأكد من وجود عميل مختار أو رقم مركبة.'})

            # find existing unpaid invoice for this client/car if any
            # Avoid reusing an unpaid invoice that was created before the last
            # delivery for this car (i.e. ensure new maintenance starts a fresh
            # billing cycle). Only reuse unpaid invoices created *after* the
            # most recent delivery_date for the car.
            invoice = None
            if car and client_obj:
                try:
                    last_delivered = car.maintenance_records.filter(delivery_date__isnull=False).order_by('-delivery_date').first()
                    if last_delivered and getattr(last_delivered, 'delivery_date', None):
                        invoice = Invoice.objects.filter(car=car, client=client_obj, paid=False, created_at__gte=last_delivered.delivery_date).order_by('-created_at').first()
                    else:
                        invoice = Invoice.objects.filter(car=car, client=client_obj, paid=False).order_by('-created_at').first()
                except Exception:
                    invoice = Invoice.objects.filter(car=car, client=client_obj, paid=False).first()
            elif client_obj:
                invoice = Invoice.objects.filter(client=client_obj, paid=False).order_by('-created_at').first()
            # Prevent creating a new maintenance when there's an open maintenance record
            try:
                if car and MaintenanceRecord.objects.filter(car=car, is_finished=False).exists():
                    return render(request, 'add_maintenance_record.html', {
                        'form': form,
                        'car_instance': car_instance,
                        'error': 'لا يمكن إنشاء صيانة جديدة: توجد صيانة مفتوحة للمركبة.'
                    })
            except Exception:
                # best-effort: if the check fails, continue and let later logic handle errors
                pass
            # capture submitted items_json early so we can decide whether to create an invoice
            items_json = request.POST.get('items_json')
            # Determine invoice number: prefer submitted value if provided, otherwise compute next
            submitted_inv = (request.POST.get('invoice_number') or '').strip()
            def _parse_inv_number(s):
                # try formats like 'INV-000123' or plain digits
                if not s:
                    return None
                s = s.strip()
                if s.upper().startswith('INV-'):
                    num = s.split('INV-')[-1]
                else:
                    num = s
                try:
                    return int(num)
                except Exception:
                    return None

            if not invoice:
                # compute a candidate invoice number based on last invoice
                last_invoice = Invoice.objects.order_by('-id').first()
                next_number = 1
                if last_invoice:
                    parsed = _parse_inv_number(last_invoice.invoice_number or '')
                    if parsed is not None:
                        next_number = parsed + 1
                    else:
                        # fallback: try numeric tail if startswith INV-
                        if last_invoice.invoice_number and last_invoice.invoice_number.startswith('INV-'):
                            try:
                                tail = int(last_invoice.invoice_number.split('INV-')[-1])
                                next_number = tail + 1
                            except Exception:
                                next_number = 1
                generated_invoice_number = f"INV-{next_number:06d}"

                # If user submitted an invoice number, try to use it (if unique). Otherwise use generated.
                use_invoice_number = generated_invoice_number
                if submitted_inv:
                    # if submitted numeric, normalize to INV- padded if needed
                    submitted_parsed = _parse_inv_number(submitted_inv)
                    if submitted_parsed is not None:
                        candidate = f"INV-{submitted_parsed:06d}"
                    else:
                        candidate = submitted_inv
                    # ensure uniqueness: if candidate already exists, fall back to generated
                    if not Invoice.objects.filter(invoice_number=candidate).exists():
                        use_invoice_number = candidate
                # Only create an actual Invoice record when there is real invoice data to store
                # (items_json present, or an explicit service/price). Do NOT create an empty
                # placeholder invoice just because an invoice number was shown or suggested.
                if items_json or service or price:
                    # Create invoice with retry on UNIQUE constraint violation
                    from django.db import IntegrityError, transaction
                    attempt = 0
                    invoice = None
                    while True:
                        try:
                            with transaction.atomic():
                                invoice = Invoice.objects.create(
                                    invoice_number=use_invoice_number,
                                    client=client_obj,
                                    car=car,
                                    amount=0,
                                    paid=False,
                                    created_at=maintenance_date
                                )
                            break
                        except IntegrityError:
                            attempt += 1
                            # bump the numeric part and try again
                            try:
                                next_number += 1
                                use_invoice_number = f"INV-{next_number:06d}"
                            except Exception:
                                # fallback to a timestamp-suffixed invoice number
                                from django.utils import timezone
                                use_invoice_number = f"INV-{int(timezone.now().timestamp())}-{attempt}"
                            if attempt > 10:
                                raise
                    # ensure invoice has client/car if available
                    try:
                        changed = False
                        if not invoice.client and client_obj:
                            invoice.client = client_obj; changed = True
                        if not invoice.car and car:
                            invoice.car = car; changed = True
                        if changed:
                            invoice.save()
                    except Exception:
                        pass
                else:
                    invoice = None
            # Debug: dump full POST for inspection
            try:
                with open('debug_post_dump.log', 'a', encoding='utf-8') as _f:
                    _f.write(repr(dict(request.POST)) + "\n")
            except Exception:
                pass
            # If the form contains item rows (items_json), persist them as InvoiceItem
            items_json = request.POST.get('items_json')
            print('DEBUG: full POST ->', repr(dict(request.POST)))
            print('DEBUG: received items_json ->', items_json)
            # Debug: log raw items_json to file for inspection
            try:
                if items_json:
                    with open('debug_items_json.log', 'a', encoding='utf-8') as _f:
                        _f.write(f"INVOICE:{invoice.id if invoice else 'none'} JSON:{items_json}\n")
            except Exception:
                pass
            if items_json:
                import json
                try:
                    items = json.loads(items_json)
                except Exception:
                    items = []
                # remove existing items for this invoice (if any)
                invoice.items.all().delete()
                total_amount = 0
                for it in items:
                    desc = (it.get('description') or '').strip()
                    try:
                        qty = float(it.get('qty') or 0)
                    except Exception:
                        qty = 0.0
                    try:
                        rate = float(it.get('rate') or 0)
                    except Exception:
                        rate = 0.0
                    try:
                        discount = float(it.get('discount') or 0)
                    except Exception:
                        discount = 0.0
                    line_total = qty * rate * (1 - discount/100.0)
                    # Skip empty rows: no description and no numeric values
                    if (not desc) and qty == 0 and rate == 0 and discount == 0:
                        continue
                    total_amount += line_total
                    InvoiceItem = None
                    try:
                        from invoices.models import InvoiceItem as II
                        InvoiceItem = II
                    except Exception:
                        InvoiceItem = None
                    if InvoiceItem:
                        InvoiceItem.objects.create(
                            invoice=invoice,
                            description=desc,
                            quantity=qty,
                            rate=rate,
                            discount=discount,
                            total=round(line_total, 3)
                        )
                # update invoice total
                invoice.amount = round(total_amount, 3)
                invoice.save()
                # Previously the code created a placeholder Service and MaintenanceRecord
                # when `items_json` was present but no explicit `service` field was
                # provided. That produced a synthetic service named
                # 'عُمل/قطع (مُنشأ من فاتورة)' and led to unexpected invoice items.
                #
                # We no longer create that placeholder Service/MaintenanceRecord here.
                # InvoiceItem rows created from `items_json` are sufficient and the
                # car status will be updated below. Any explicit MaintenanceRecord
                # should still be created when the form provides `service`/`price`.
            # Create a maintenance record only if service/price were provided via form
            if service or price:
                MaintenanceRecord.objects.create(
                    car=car,
                    service=service,
                    price=price or 0,
                    notes=notes,
                    created_at=maintenance_date,
                    invoice=invoice
                )
            else:
                # If the user did NOT provide an explicit `service`/`price` but DID
                # submit `items_json`, we create InvoiceItem rows above and should
                # NOT create a single placeholder MaintenanceRecord that summarizes
                # the whole invoice — doing so leads to duplicate invoice items
                # later when the code reconciles maintenance records with invoice
                # items. Therefore only create a placeholder MaintenanceRecord when
                # there are NO `items_json` rows (i.e. truly no item data was
                # submitted).
                try:
                    if invoice and car and not items_json:
                        try:
                            from services.models import Department
                        except Exception:
                            Department = None
                        dept = None
                        try:
                            if Department:
                                dept = Department.objects.first()
                                if not dept:
                                    dept = Department.objects.create(name='General')
                        except Exception:
                            dept = None
                        # create or reuse a placeholder service
                        try:
                            svc_name = 'Invoice items (created)'
                            svc_defaults = {'default_price': float(invoice.amount or 0), 'department': dept, 'car': car}
                            svc, created = Service.objects.get_or_create(name=svc_name, defaults=svc_defaults)
                            if not created:
                                # ensure price/car are sensible
                                try:
                                    svc.default_price = float(invoice.amount or svc.default_price)
                                    if not svc.car and car:
                                        svc.car = car
                                    svc.save()
                                except Exception:
                                    pass
                            MaintenanceRecord.objects.create(
                                car=car,
                                service=svc,
                                price=float(invoice.amount or 0),
                                notes='Created from invoice items',
                                created_at=maintenance_date,
                                invoice=invoice
                            )
                        except Exception:
                            # best-effort: if creating a placeholder service fails, skip
                            pass
                except Exception:
                    pass
            # Ensure car has a sensible initial status (avoid legacy unset/unknown values)
            try:
                # Ensure cars with no or invalid status are initialized to 'waiting'
                if car:
                    cur_status = getattr(car, 'status', None)
                    if not cur_status or cur_status not in ['done', 'pending_payment', 'in_progress', 'waiting']:
                        try:
                            with open('debug_car_status.log', 'a', encoding='utf-8') as _f:
                                _f.write(f"FINAL-CHANGE: car_id={car.id} was {cur_status}, setting to waiting\n")
                        except Exception:
                            pass
                        car.status = 'waiting'
                        car.save()
            except Exception:
                pass
            # After creating invoice/items or maintenance records, transition car status
            try:
                if car:
                    # if there are invoice items or a maintenance record just created,
                    # move from 'waiting' -> 'in_progress'
                    has_items = bool(items_json)
                    has_service = bool(service or price)
                    current = (getattr(car, 'status', '') or '').lower()
                    if (has_items or has_service) and current in ['waiting', 'active', '']:
                        car.status = 'in_progress'
                        car.save()
                        try:
                            with open('debug_car_status.log', 'a', encoding='utf-8') as _f:
                                _f.write(f"STATUS-TRANSITION: car_id={car.id} -> in_progress\n")
                        except Exception:
                            pass
            except Exception:
                pass
            if service and invoice and service.pk not in invoice.services.values_list('pk', flat=True):
                invoice.services.add(service.pk)
            # If we created or have an invoice, recompute its amounts and ensure
            # maintenance records are represented as invoice items. If invoice is
            # None (no items/service submitted), skip these steps to avoid errors.
            if invoice:
                # Recompute invoice.amount deterministically from InvoiceItem totals when possible.
                try:
                    from django.db.models import Sum
                    item_total = invoice.items.aggregate(total=Sum('total'))['total'] or 0
                    # item_total is Decimal or numeric; store as rounded float-compatible value
                    invoice.amount = float(item_total)
                    try:
                        # If invoice/items_json provided and there are no maintenance
                        # records linked to that invoice, create a representative
                        # MaintenanceRecord so the workflow (filters/derive logic)
                        # has a persistent record to reference.
                        if invoice and car:
                            # If items_json was provided, prefer creating a single
                            # maintenance record representing the invoice items.
                            if items_json:
                                # only create when no existing maintenance records
                                if not invoice.maintenance_records.exists():
                                    try:
                                        from services.models import Department
                                    except Exception:
                                        Department = None
                                    dept = None
                                    try:
                                        if Department:
                                            dept = Department.objects.first()
                                            if not dept:
                                                dept = Department.objects.create(name='General')
                                    except Exception:
                                        dept = None
                                    # create or reuse a placeholder service
                                    try:
                                        svc_name = 'Invoice items (created)'
                                        svc_defaults = {'default_price': float(invoice.amount or 0), 'department': dept, 'car': car}
                                        svc, created = Service.objects.get_or_create(name=svc_name, defaults=svc_defaults)
                                        if not created:
                                            try:
                                                svc.default_price = float(invoice.amount or svc.default_price)
                                                if not svc.car and car:
                                                    svc.car = car
                                                svc.save()
                                            except Exception:
                                                pass
                                        # create a single maintenance record representing the invoice
                                        from django.utils import timezone
                                        mr = MaintenanceRecord.objects.create(
                                            car=car,
                                            service=svc,
                                            price=float(invoice.amount or 0),
                                            notes='Created from invoice items',
                                            created_at=maintenance_date,
                                            invoice=invoice,
                                            is_finished=bool(invoice.paid),
                                            ready_at=(invoice.created_at if invoice.paid else None),
                                            delivery_date=(timezone.now() if invoice.paid else None)
                                        )
                                    except Exception:
                                        pass
                            else:
                                # items_json not present: existing placeholder creation follows old logic
                                try:
                                    from services.models import Department
                                except Exception:
                                    Department = None
                                dept = None
                                try:
                                    if Department:
                                        dept = Department.objects.first()
                                        if not dept:
                                            dept = Department.objects.create(name='General')
                                except Exception:
                                    dept = None
                                try:
                                    svc_name = 'Invoice items (created)'
                                    svc_defaults = {'default_price': float(invoice.amount or 0), 'department': dept, 'car': car}
                                    svc, created = Service.objects.get_or_create(name=svc_name, defaults=svc_defaults)
                                    if not created:
                                        try:
                                            svc.default_price = float(invoice.amount or svc.default_price)
                                            if not svc.car and car:
                                                svc.car = car
                                            svc.save()
                                        except Exception:
                                            pass
                                    from django.utils import timezone
                                    MaintenanceRecord.objects.create(
                                        car=car,
                                        service=svc,
                                        price=float(invoice.amount or 0),
                                        notes='Created from invoice',
                                        created_at=maintenance_date,
                                        invoice=invoice,
                                        is_finished=bool(invoice.paid),
                                        ready_at=(invoice.created_at if invoice.paid else None),
                                        delivery_date=(timezone.now() if invoice.paid else None)
                                    )
                                except Exception:
                                    pass
                    except Exception:
                        pass
                except Exception:
                    pass
                # Do NOT mark car as 'pending_payment' here. Pending/payment state
                # should be set explicitly when maintenance is finished or when the
                # car is delivered. This prevents add-maintenance (which may create
                # invoices/items) from immediately flipping the car to pending_payment.
                pass
            # Redirect based on which action button was used (save_draft vs save_send)
            try:
                with open('debug_post_actions.log', 'a', encoding='utf-8') as _f:
                    _f.write(f"POST-COMPLETE: car_id={getattr(car,'id',None)} status={getattr(car,'status',None)} invoice_id={getattr(invoice,'id',None) if invoice else 'none'} amount={getattr(invoice,'amount',None) if invoice else 'none'}\n")
            except Exception:
                pass
            action = (request.POST.get('action') or '').strip()
            if action == 'save_send':
                return redirect('/dashboard/')
            if car:
                return redirect(f'/maintenance/?plate_number={car.plate_number}')
            return redirect('/maintenance/')
    else:
        form = AddMaintenanceForm(initial=initial)
        try:
            sel_cid_get = request.GET.get('selected_client_id')
            if car_instance and getattr(car_instance, 'client', None):
                form.fields['selected_client_car'].queryset = Car.objects.filter(client=car_instance.client)
            elif sel_cid_get:
                try:
                    from clients.models import Client
                    cl = Client.objects.filter(id=sel_cid_get).first()
                    if cl:
                        form.fields['selected_client_car'].queryset = Car.objects.filter(client=cl)
                except Exception:
                    pass
        except Exception:
            pass
    # Provide a small client list for frontend autocomplete (no extra endpoint required)
    clients_sample = []
    try:
        from clients.models import Client
        for c in Client.objects.all()[:200]:
            plates = [car.plate_number for car in c.cars.all()[:5] if car.plate_number]
            cars_list = [{'id': car.id, 'plate': car.plate_number} for car in c.cars.all()[:20] if car.plate_number]
            clients_sample.append({'id': c.id, 'name': f"{c.first_name} {c.last_name or ''}".strip(), 'phone': getattr(c, 'phone', ''), 'plates': plates, 'cars': cars_list})
    except Exception:
        clients_sample = []
    # compute next invoice number for prefilling the form
    next_invoice_number = ''
    try:
        last_invoice = Invoice.objects.order_by('-id').first()
        if last_invoice:
            # try parse trailing number
            if last_invoice.invoice_number and last_invoice.invoice_number.upper().startswith('INV-'):
                try:
                    last_num = int(last_invoice.invoice_number.split('INV-')[-1])
                    next_invoice_number = f"INV-{(last_num+1):06d}"
                except Exception:
                    next_invoice_number = ''
            else:
                # if it's numeric, increment
                try:
                    v = int((last_invoice.invoice_number or '').strip())
                    next_invoice_number = f"INV-{(v+1):06d}"
                except Exception:
                    next_invoice_number = ''
    except Exception:
        next_invoice_number = ''
    # If there are no previous invoices, default to INV-000001 for clarity
    if not next_invoice_number:
        next_invoice_number = 'INV-000001'
    return render(request, 'add_maintenance_record.html', {'form': form, 'car_instance': car_instance, 'clients_sample': clients_sample, 'next_invoice_number': next_invoice_number})


# Search clients (autocomplete) - returns small JSON list
def search_clients(request):
    q = request.GET.get('q', '').strip()
    results = []
    from clients.models import Client
    if q:
        qs = Client.objects.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(phone__icontains=q) | Q(cars__plate_number__icontains=q)
        ).distinct()[:50]
    else:
        qs = Client.objects.all().order_by('-id')[:50]
    for c in qs:
        plates = [car.plate_number for car in c.cars.all()[:5] if car.plate_number]
        results.append({'id': c.id, 'name': f"{c.first_name} {c.last_name or ''}".strip(), 'phone': getattr(c, 'phone', ''), 'plates': plates})
    return JsonResponse({'results': results})
