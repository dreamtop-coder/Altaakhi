from django.views.decorators.http import require_GET
from django.db.models import Q
import logging

# module logger
logger = logging.getLogger(__name__)

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


def get_services_json(request):
    """Return simple JSON list of services matching query for autocomplete.
    Format matches inventory JSON: { results: [ {id, name, price, code, track_stock, quantity} ] }
    """
    q = (request.GET.get('q') or '').strip()
    qs = Service.objects.all().order_by('name')
    if q:
        qs = qs.filter(name__icontains=q)

    # Debug: log and include matched count to help diagnose frontend empty results
    try:
        logger.debug('get_services_json: q=%r matched=%d', q, qs.count())
    except Exception:
        pass

    # limit and return lightweight structures
    svc_vals = list(qs.values('id', 'name', 'default_price')[:100])
    results = []
    for s in svc_vals:
        results.append({
            'id': s.get('id'),
            'name': s.get('name') or '',
            'sale_price': float(s.get('default_price')) if s.get('default_price') is not None else None,
            'code': '',
            'track_stock': False,
            'quantity': None,
        })
    # Include lightweight debug info temporarily to aid diagnosis in-browser
    try:
        debug_info = {'q': q, 'matched': len(results)}
    except Exception:
        debug_info = {'q': q}
    return JsonResponse({'results': results, 'debug': debug_info})
from django.shortcuts import render, redirect
from .forms_add_maintenance import AddMaintenanceForm

from .maintenance_models import MaintenanceRecord
from invoices.models import Invoice

# صفحة إضافة سجل صيانة لمركبة

def add_maintenance_record(request):
    from .models import Car
    car_id = request.GET.get('car_id')
    car_instance = None
    # locked_car: logical guard layer when this view is opened with a car_id
    locked_car = None
    initial = {}
    if car_id:
        try:
            car_instance = Car.objects.get(id=car_id)
            locked_car = car_instance
            initial['plate_number'] = car_instance.plate_number
        except Car.DoesNotExist:
            car_instance = None
    # Shadow: resolve ContextGuard for monitoring/comparison (no enforcement yet)
    try:
        try:
            from services.context_guard import ContextGuard
            ctx = ContextGuard.resolve(request, model='maintenance')
        except Exception:
            ctx = {'locked': False, 'car': None, 'customer': None}
        try:
            with open('debug_context_guard.log', 'a', encoding='utf-8') as _f:
                _f.write(
                    f"CTX_GUARD: car_id_param={car_id} "
                    f"car_instance_id={getattr(car_instance,'id',None)} "
                    f"ctx_locked={ctx.get('locked')} ctx_car_id={getattr(ctx.get('car'), 'id', None)} "
                    f"ctx_customer_id={getattr(ctx.get('customer'), 'id', None)}\n"
                )
        except Exception:
            pass
    except Exception:
        ctx = {'locked': False, 'car': None, 'customer': None}
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
        # Controlled enforcement via ContextGuard behind feature toggle.
        try:
            from django.conf import settings
            if getattr(settings, 'CONTEXT_GUARD_ENFORCE', False) or getattr(settings, 'ENABLE_CONTEXT_GUARD_POST_OVERRIDE', False):
                try:
                    from services.context_guard import ContextGuard
                    ContextGuard.enforce_request_post(request, ctx)
                    try:
                        with open('debug_context_guard.log', 'a', encoding='utf-8') as _f:
                            _f.write(f"ENFORCE_APPLIED: enforced_by=ContextGuard\n")
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            pass

        # Existing local fallback: if this page was opened with a `car_id`, treat
        # that as the source of truth and ensure submitted client/car/plate values
        # are set. Keep this as a fallback even when the ContextGuard enforcement
        # is enabled so we have deterministic behavior and an easy rollback.
        if locked_car:
            try:
                p = request.POST.copy()
                if getattr(locked_car, 'client', None):
                    p['selected_client_id'] = str(locked_car.client.id)
                p['selected_client_car'] = str(locked_car.id)
                p['plate_number'] = locked_car.plate_number or ''
                # replace request.POST locally so downstream code reads the enforced values
                request.POST = p
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

        # Evaluate form validity once and log results for debugging failing posts
        try:
            valid = form.is_valid()
        except Exception:
            valid = False
        try:
            with open('debug_post_dump.log', 'a', encoding='utf-8') as _f:
                _f.write(f"FORM-VALID: {valid} client_for_q={getattr(client_for_queryset,'id',None)} sel_cid={request.POST.get('selected_client_id')} resolved_car_by_form={getattr(form.cleaned_data if hasattr(form,'cleaned_data') else {}, 'get', lambda k, d=None: None)('selected_client_car')} form_errors={getattr(form,'errors',None)}\n")
        except Exception:
            pass

        if valid:
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

            # Server-side guard: if this page was opened with a locked car, ensure
            # the resolved client/car pair matches the locked context. This defends
            # against malicious manual POSTs that attempt to change the client.
            if locked_car:
                try:
                    if car and client_obj:
                        if int(getattr(car, 'id', 0)) != int(getattr(locked_car, 'id', 0)) or int(getattr(client_obj, 'id', 0)) != int(getattr(getattr(locked_car, 'client', None), 'id', 0)):
                            return render(request, 'add_maintenance_record.html', {
                                'form': form,
                                'car_instance': car_instance,
                                'clients_sample': [],
                                'error': 'تم قفل هذه الصفحة على مركبة محددة. لإجراء تغييرات، اضغط "تغيير المركبة".',
                                'invoice_type': 'maintenance'
                            })
                except Exception:
                    pass

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
                                'error': 'العميل لديه أكثر من مركبة، الرجاء اختيار رقم اللوحة أو تحديد المركبة من القائمة.',
                                'invoice_type': 'maintenance'
                            })
                except Exception:
                    pass

            if not client_obj:
                return render(request, 'add_maintenance_record.html', {'form': form, 'car_instance': car_instance, 'error': 'تأكد من وجود عميل مختار أو رقم مركبة.', 'invoice_type': 'maintenance'})

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
                        'error': 'لا يمكن إنشاء صيانة جديدة: توجد صيانة مفتوحة للمركبة.',
                        'invoice_type': 'maintenance'
                    })
            except Exception:
                # best-effort: if the check fails, continue and let later logic handle errors
                pass
            # capture submitted items_json early so we can decide whether to create an invoice
            # Some browsers/forms may submit multiple `items_json` fields (one empty),
            # so prefer the first non-empty value from getlist()
            try:
                vals = request.POST.getlist('items_json') if hasattr(request.POST, 'getlist') else [request.POST.get('items_json')]
                items_json = None
                # Prefer a meaningful items_json value: non-empty and not a literal empty list '[]' or 'null'
                for v in reversed(vals):
                    if v and str(v).strip() and str(v).strip() not in ['[]', 'null']:
                        items_json = v
                        break
                # fallback: accept any non-empty value
                if not items_json:
                    for v in reversed(vals):
                        if v and str(v).strip():
                            items_json = v
                            break
            except Exception:
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
                # Compute a candidate invoice number but do NOT create the Invoice
                # record here. Creation will be deferred until we persist items
                # (inside a single transaction) or when a service-only maintenance
                # record is being created below. This prevents orphan/empty
                # invoices when item processing fails later.
                try:
                    last_invoice = Invoice.objects.order_by('-id').first()
                    next_number = 1
                    if last_invoice:
                        parsed = _parse_inv_number(last_invoice.invoice_number or '')
                        if parsed is not None:
                            next_number = parsed + 1
                        else:
                            if last_invoice.invoice_number and last_invoice.invoice_number.startswith('INV-'):
                                try:
                                    tail = int(last_invoice.invoice_number.split('INV-')[-1])
                                    next_number = tail + 1
                                except Exception:
                                    next_number = 1
                    generated_invoice_number = f"INV-{next_number:06d}"
                    use_invoice_number = generated_invoice_number
                    if submitted_inv:
                        submitted_parsed = _parse_inv_number(submitted_inv)
                        if submitted_parsed is not None:
                            candidate = f"INV-{submitted_parsed:06d}"
                        else:
                            candidate = submitted_inv
                        if not Invoice.objects.filter(invoice_number=candidate).exists():
                            use_invoice_number = candidate
                except Exception as _exc:
                    try:
                        with open('debug_post_dump.log', 'a', encoding='utf-8') as _f:
                            _f.write(f"INVOICE-CREATE-ERROR: {_exc!r} items_json_present={bool(items_json)} service={bool(service)} price={bool(price)}\n")
                    except Exception:
                        pass
                    use_invoice_number = submitted_inv or 'INV-000001'
                # Log that we have a candidate invoice number (invoice not created yet)
                try:
                    with open('debug_post_dump.log', 'a', encoding='utf-8') as _f:
                        _f.write(f"INVOICE-CREATED-DEBUG: invoice_id={getattr(invoice,'id',None)} items_json_present={bool(items_json)} use_invoice_number={locals().get('use_invoice_number',None)}\n")
                except Exception:
                    pass
            # Debug: dump full POST for inspection
            try:
                with open('debug_post_dump.log', 'a', encoding='utf-8') as _f:
                    _f.write(repr(dict(request.POST)) + "\n")
            except Exception:
                pass
            # If the form contains item rows (items_json), persist them as InvoiceItem
            # Re-evaluate multi-valued items_json similarly to above to be safe
            try:
                vals2 = request.POST.getlist('items_json') if hasattr(request.POST, 'getlist') else [request.POST.get('items_json')]
                items_json = None
                # Prefer a meaningful items_json value: non-empty and not a literal empty list '[]' or 'null'
                for v in reversed(vals2):
                    if v and str(v).strip() and str(v).strip() not in ['[]', 'null']:
                        items_json = v
                        break
                # fallback: accept any non-empty value
                if not items_json:
                    for v in reversed(vals2):
                        if v and str(v).strip():
                            items_json = v
                            break
            except Exception:
                items_json = request.POST.get('items_json')
            try:
                logger.debug('DEBUG: full POST -> %s', repr(dict(request.POST)))
            except Exception:
                pass
            try:
                logger.debug('DEBUG: received items_json -> %s', items_json)
            except Exception:
                pass
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

                from django.db import transaction
                try:
                    from inventory.utils import check_items_availability, apply_inventory_changes_for_invoice
                except Exception:
                    check_items_availability = None
                    apply_inventory_changes_for_invoice = None

                try:
                    # Perform invoice + items + inventory update + maintenance record in one transaction
                    with transaction.atomic():
                        # Ensure an invoice exists for this maintenance POST
                        if not invoice:
                            invoice = Invoice.objects.create(
                                invoice_number=use_invoice_number,
                                client=client_obj,
                                car=car,
                                amount=0,
                                paid=False,
                                created_at=maintenance_date,
                                type='maintenance'
                            )

                        # Validate availability before creating items
                        if check_items_availability:
                            shortages = check_items_availability(items, None)
                            if shortages:
                                first = shortages[0]
                                from django.http import HttpResponseBadRequest
                                pname = getattr(first[0], 'name', '') if first and first[0] else ''
                                msg = f'الكمية غير متوفرة: {pname}. المتوفر: {first[1]} المطلوب: {first[2]}'
                                return HttpResponseBadRequest(msg)

                        # Remove any existing items for this invoice and recreate
                        try:
                            invoice.items.all().delete()
                        except Exception:
                            pass

                        total_amount = 0
                        from invoices.models import InvoiceItem as II
                        from services.models import Service as ServiceModel
                        from inventory.models import Part as InventoryPart

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
                            line_total = qty * rate * (1 - discount / 100.0)
                            if (not desc) and qty == 0 and rate == 0 and discount == 0:
                                continue
                            total_amount += line_total

                            service = None
                            part = None
                            try:
                                service_id = it.get('service_id')
                                part_id = it.get('part_id')
                            except Exception:
                                service_id = None
                                part_id = None
                            if service_id:
                                try:
                                    service = ServiceModel.objects.filter(id=service_id).first()
                                except Exception:
                                    service = None
                            if part_id:
                                try:
                                    part = InventoryPart.objects.filter(id=part_id).first()
                                except Exception:
                                    part = None

                            item_type = 'service' if service else 'part'

                            II.objects.create(
                                invoice=invoice,
                                service=service,
                                part=part,
                                item_type=item_type,
                                description=desc[:255],
                                quantity=qty,
                                rate=rate,
                                discount=discount,
                                total=round(line_total, 3)
                            )

                        # decrement inventory for all created items (parts only)
                        if apply_inventory_changes_for_invoice:
                            apply_inventory_changes_for_invoice(items, decrement=True)

                        invoice.amount = round(total_amount, 3)
                        invoice.save()

                        # Create a MaintenanceRecord linked to this invoice so worklog exists
                        # Prefer to attach a real Service from the submitted `items_json`
                        # (first service-type item) rather than creating a placeholder
                        try:
                            service_obj = None
                            try:
                                # `ServiceModel` was imported above when building items
                                svc_model = ServiceModel
                            except Exception:
                                try:
                                    from services.models import Service as svc_model
                                except Exception:
                                    svc_model = None

                            if svc_model and isinstance(items, list):
                                for it in items:
                                    # accept either numeric id keys or string keys
                                    sid = None
                                    try:
                                        sid = it.get('service_id')
                                    except Exception:
                                        sid = None
                                    if sid:
                                        try:
                                            service_obj = svc_model.objects.filter(id=sid).first()
                                        except Exception:
                                            service_obj = None
                                    # fallback: match by description/name when no id present
                                    if not service_obj:
                                        name = (it.get('description') or '').strip()
                                        if name:
                                            try:
                                                service_obj = svc_model.objects.filter(name__iexact=name).first()
                                            except Exception:
                                                service_obj = None
                                    if service_obj:
                                        break

                            # Only create a MaintenanceRecord for invoices that represent
                            # maintenance work. Do not create a workshop record for
                            # sales-type invoices (parts-only invoices).
                            try:
                                inv_type = getattr(invoice, 'type', None)
                            except Exception:
                                inv_type = None
                            if car and inv_type == 'maintenance':
                                from .maintenance_models import MaintenanceRecord as _MR
                                mr = _MR.objects.create(
                                    car=car,
                                    service=service_obj,
                                    price=float(invoice.amount or 0),
                                    notes='Created from invoice items',
                                    created_at=maintenance_date,
                                    invoice=invoice,
                                )
                        except Exception:
                            pass

                except Exception as e:
                    # if validation/creation fails, show a generic error and log
                    try:
                        from django.contrib import messages
                        messages.error(request, 'فشل في حفظ عناصر الفاتورة. حاول لاحقاً.')
                    except Exception:
                        pass
                    try:
                        with open('debug_post_dump.log', 'a', encoding='utf-8') as _f:
                            _f.write(f"ITEMS-PROCESS-ERROR: {e!r} items_json={items_json}\n")
                    except Exception:
                        pass
                    params = f'?car_id={car.id}' if car and getattr(car, 'id', None) else ''
                    try:
                        return redirect(request.path + params)
                    except Exception:
                        return redirect('/maintenance/add/' + params)
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
                try:
                    from django.db import transaction
                    from invoices.models import InvoiceItem
                    with transaction.atomic():
                        # Prefer using the invoice creation date as the maintenance
                        # record date when an invoice exists (keeps dates consistent).
                        created_at_value = (getattr(invoice, 'created_at', None) if invoice else None) or maintenance_date
                        # Ensure an Invoice exists for service-only submissions.
                        # If invoice was deferred above, create it here inside the
                        # transaction so invoice + maintenance record are atomic.
                        if not invoice:
                            try:
                                invoice = Invoice.objects.create(
                                    invoice_number=use_invoice_number,
                                    client=client_obj,
                                    car=car,
                                    amount=0,
                                    paid=False,
                                    created_at=created_at_value,
                                    type='maintenance'
                                )
                            except Exception:
                                # fallback: continue without invoice (best-effort)
                                invoice = None
                        mr = MaintenanceRecord.objects.create(
                            car=car,
                            service=service,
                            price=price or 0,
                            notes=notes,
                            created_at=created_at_value,
                            invoice=invoice
                        )
                        # If an invoice exists but there are no explicit items_json rows,
                        # create a corresponding InvoiceItem so invoices always have items.
                        try:
                            if invoice and not items_json:
                                desc = service.name if service else (notes or '')
                                ii = InvoiceItem.objects.create(
                                    invoice=invoice,
                                    service=service,
                                    description=desc[:255],
                                    quantity=1,
                                    rate=mr.price or 0,
                                    discount=0,
                                    total=mr.price or 0,
                                    item_type=('service' if service else 'part')
                                )
                                # Ensure total is computed from rate * quantity (and discount if present)
                                try:
                                    from decimal import Decimal
                                    q = Decimal(ii.quantity)
                                    r = Decimal(ii.rate)
                                    d = Decimal(ii.discount or 0) / Decimal('100')
                                    ii.total = (q * r * (Decimal('1') - d)).quantize(Decimal('0.001'))
                                    ii.save()
                                except Exception:
                                    try:
                                        ii.total = ii.rate * ii.quantity
                                        ii.save()
                                    except Exception:
                                        pass
                                # Recompute invoice amount deterministically using model helper if available
                                try:
                                    invoice.recalc_amount()
                                except Exception:
                                    from django.db.models import Sum
                                    invoice.amount = float(invoice.items.aggregate(total=Sum('total'))['total'] or 0)
                                    invoice.save()
                        except Exception:
                            pass
                except Exception:
                    # best-effort: still try to create a MaintenanceRecord if transaction fails
                    try:
                        mr = MaintenanceRecord.objects.create(
                            car=car,
                            service=service,
                            price=price or 0,
                            notes=notes,
                            created_at=maintenance_date,
                            invoice=invoice
                        )
                    except Exception:
                        pass
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
                        # create a per-invoice placeholder service to avoid
                        # reusing a global "Invoice items (created)" service
                        try:
                            svc_suffix = (getattr(invoice, 'invoice_number', None) or locals().get('use_invoice_number') or f"inv-{getattr(invoice,'id', 'unknown')}")
                            svc_name = f'Invoice items (created) - {svc_suffix}'
                            # do NOT attach the placeholder service to the car
                            svc_defaults = {'default_price': float(invoice.amount or 0), 'department': dept}
                            svc, created = Service.objects.get_or_create(name=svc_name, defaults=svc_defaults)
                            if not created:
                                try:
                                    svc.default_price = float(invoice.amount or svc.default_price)
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
                    # Only transition car status to 'in_progress' for maintenance-type
                    # invoices. Sales invoices (parts-only) should not mark the car
                    # as being worked on in the workshop.
                    try:
                        inv_type = getattr(invoice, 'type', None)
                    except Exception:
                        inv_type = None
                    # if there are invoice items or a maintenance record just created,
                    # move from 'waiting' -> 'in_progress' when this is a maintenance invoice
                    has_items = bool(items_json)
                    has_service = bool(service or price)
                    current = (getattr(car, 'status', '') or '').lower()
                    if inv_type == 'maintenance' and (has_items or has_service) and current in ['waiting', 'active', '']:
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
                # Safety: ensure invoice.car is set when possible. Some POSTs
                # may have resolved a `car` earlier into the local `car` var
                # or provide a `plate_number` in the form — attach that to
                # the invoice so maintenance records are correctly linked.
                try:
                    if not invoice.car:
                        if car:
                            invoice.car = car
                            invoice.save()
                        else:
                            plate_try = (request.POST.get('plate_number') or '').strip()
                            if plate_try:
                                try:
                                    from .models import Car as CarModel
                                    found = CarModel.objects.filter(plate_number__iexact=plate_try).first()
                                    if found:
                                        invoice.car = found
                                        invoice.save()
                                        car = found
                                except Exception:
                                    pass
                except Exception:
                    pass
                # Recompute invoice.amount deterministically from InvoiceItem totals when possible.
                try:
                    from django.db.models import Sum
                    item_total = invoice.items.aggregate(total=Sum('total'))['total'] or 0
                    # item_total is Decimal or numeric; store as rounded float-compatible value
                    invoice.amount = float(item_total)
                    try:
                        # ensure any existing maintenance records linked to this invoice
                        # have their `price` set to the invoice amount (fixes cases
                        # where MR was created earlier with price=0)
                        try:
                            invoice.maintenance_records.filter(price__lte=0).update(price=float(invoice.amount or 0))
                        except Exception:
                            pass
                        # If invoice/items_json provided and there are no maintenance
                        # records linked to that invoice, create a representative
                        # MaintenanceRecord so the workflow (filters/derive logic)
                        # has a persistent record to reference.
                        if invoice and car:
                            # Only create maintenance records representing invoice items
                            # when the invoice is a maintenance-type invoice. Sales
                            # invoices (parts-only) should not create workshop records.
                            try:
                                inv_type = getattr(invoice, 'type', None)
                            except Exception:
                                inv_type = None
                            # If items_json was provided, prefer creating a single
                            # maintenance record representing the invoice items.
                            if items_json and inv_type == 'maintenance':
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
                                        svc_suffix = (getattr(invoice, 'invoice_number', None) or locals().get('use_invoice_number') or f"inv-{getattr(invoice,'id', 'unknown')}")
                                        svc_name = f'Invoice items (created) - {svc_suffix}'
                                        svc_defaults = {'default_price': float(invoice.amount or 0), 'department': dept}
                                        svc, created = Service.objects.get_or_create(name=svc_name, defaults=svc_defaults)
                                        if not created:
                                            try:
                                                svc.default_price = float(invoice.amount or svc.default_price)
                                                svc.save()
                                            except Exception:
                                                pass
                                        # create a single maintenance record representing the invoice
                                        from django.utils import timezone
                                        created_at_value = (getattr(invoice, 'created_at', None) if invoice else None) or maintenance_date
                                        mr = MaintenanceRecord.objects.create(
                                            car=car,
                                            service=svc,
                                            price=float(invoice.amount or 0),
                                            notes='Created from invoice items',
                                            created_at=created_at_value,
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
                                    svc_suffix = (getattr(invoice, 'invoice_number', None) or locals().get('use_invoice_number') or f"inv-{getattr(invoice,'id', 'unknown')}")
                                    svc_name = f'Invoice items (created) - {svc_suffix}'
                                    svc_defaults = {'default_price': float(invoice.amount or 0), 'department': dept}
                                    svc, created = Service.objects.get_or_create(name=svc_name, defaults=svc_defaults)
                                    if not created:
                                        try:
                                            svc.default_price = float(invoice.amount or svc.default_price)
                                            svc.save()
                                        except Exception:
                                            pass
                                    from django.utils import timezone
                                    created_at_value = (getattr(invoice, 'created_at', None) if invoice else None) or maintenance_date
                                    MaintenanceRecord.objects.create(
                                        car=car,
                                        service=svc,
                                        price=float(invoice.amount or 0),
                                        notes='Created from invoice',
                                        created_at=created_at_value,
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
                # If an invoice was created as part of this POST, redirect
                # to its print view so the user can print immediately.
                try:
                    if invoice and getattr(invoice, 'id', None):
                        return redirect(f'/invoices/print/{invoice.id}/')
                except Exception:
                    pass
                # Redirect back to maintenance list filtered by plate (avoid /dashboard/)
                if car and getattr(car, 'plate_number', None):
                    return redirect(f'/maintenance/?plate_number={car.plate_number}')
                return redirect('/maintenance/')
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
            cars_list = []
            for car in c.cars.all()[:20]:
                if not car.plate_number:
                    continue
                cars_list.append({
                    'id': car.id,
                    'plate': car.plate_number,
                    'brand': car.brand.name if getattr(car, 'brand', None) else '',
                    'model': car.model.name if getattr(car, 'model', None) else ''
                })
            clients_sample.append({'id': c.id, 'name': f"{c.first_name} {c.last_name or ''}".strip(), 'phone': getattr(c, 'phone', ''), 'plates': plates, 'cars': cars_list})
    except Exception:
        clients_sample = []
    # compute next invoice number for prefilling the form
    next_invoice_number = ''
    last_invoice_number = ''
    try:
        last_invoice = Invoice.objects.order_by('-id').first()
        if last_invoice:
            # try parse trailing number
            try:
                last_invoice_number = last_invoice.invoice_number or ''
            except Exception:
                last_invoice_number = ''
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
    return render(request, 'add_maintenance_record.html', {'form': form, 'car_instance': car_instance, 'clients_sample': clients_sample, 'next_invoice_number': next_invoice_number, 'invoice_type': 'maintenance'})


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
