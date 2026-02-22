from django.views.decorators.http import require_GET

@require_GET
def bookings_clients(request):
	from bookings.models import Booking
	# عرض كل الحجوزات الفعلية (status='pending')
	bookings = Booking.objects.select_related('car').filter(status='pending').order_by('-service_date')
	from django.template.loader import render_to_string
	bookings_count = len(bookings)
	html = render_to_string('bookings_clients_list.html', {'bookings': bookings, 'bookings_count': bookings_count})
	from django.http import HttpResponse
	return HttpResponse(html)
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

# Endpoint لإرجاع عدد السيارات المنتهية (sold)
def get_done_count(request):
	from .models import Car
	count = Car.objects.filter(status='done').count()
	paid_waiting = Car.objects.filter(status='paid_waiting_collection').count()
	return JsonResponse({'done_count': count, 'paid_waiting_count': paid_waiting})
from .forms_edit_maintenance import EditMaintenanceRecordForm
# تعديل سجل الصيانة
def edit_maintenance_record_fields(request, record_id):
	from .maintenance_models import MaintenanceRecord
	record = get_object_or_404(MaintenanceRecord, id=record_id)
	if request.method == 'POST':
		form = EditMaintenanceRecordForm(request.POST, instance=record)
		if form.is_valid():
			form.save()
			from django.contrib import messages
			messages.success(request, 'تم تعديل سجل الصيانة بنجاح.')
			return redirect('cars:maintenance_list')
	else:
		form = EditMaintenanceRecordForm(instance=record)
	return render(request, 'edit_maintenance_record_fields.html', {'form': form, 'record': record})
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from .models import Car
from django.views.decorators.http import require_POST as _require_POST
from django.contrib.auth.decorators import login_required as _login_required
from django.template.loader import render_to_string
from invoices.models import Invoice
from datetime import timedelta
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect

def get_work_duration_dates(car):
    """
    احسب تاريخ البداية والنهاية للعمل الفعلي للسيارة.
    """
    maintenance_records = list(car.maintenance_records.all().order_by('created_at'))
    if not maintenance_records:
        return None, None
    start = maintenance_records[0].created_at
    # إذا هناك فاتورة مدفوعة، استخدم تاريخ الدفع
    paid_invoices = car.invoices.filter(paid=True).order_by('-created_at')
    if paid_invoices.exists():
        last_paid = paid_invoices.first()
        last_payment = last_paid.payments.filter(status='paid').order_by('-payment_date').first()
        if last_payment:
            end = last_payment.payment_date
            return start, end
    # إذا لا يوجد فاتورة مدفوعة، استخدم آخر صيانة منتهية
    finished_records = [r for r in maintenance_records if r.is_finished]
    if finished_records:
        end = finished_records[-1].created_at
        return start, end
    # إذا لا يوجد شيء، احسب حتى الآن
    from django.utils import timezone
    return start, timezone.now()

def get_work_duration_days(car):
	"""
	احسب مدة العمل بالأيام (يوم واحد إذا نفس اليوم، يومين إذا فرق يوم، ...)
	"""
	maintenance_records = list(car.maintenance_records.all().order_by('created_at'))
	if not maintenance_records:
		return None
	start = maintenance_records[0].created_at
	# إذا هناك فاتورة مدفوعة، استخدم تاريخ الدفع
	paid_invoices = car.invoices.filter(paid=True).order_by('-created_at')
	if paid_invoices.exists():
		last_paid = paid_invoices.first()
		last_payment = last_paid.payments.filter(status='paid').order_by('-payment_date').first()
		if last_payment:
			end = last_payment.payment_date
			days = (end.date() - start.date()).days + 1
			if days < 0:
				return None
			return days
	# إذا لا يوجد فاتورة مدفوعة، استخدم آخر صيانة منتهية
	finished_records = [r for r in maintenance_records if r.is_finished]
	if finished_records:
		end = finished_records[-1].created_at
		days = (end.date() - start.date()).days + 1
		if days < 0:
			return None
		return days
	# إذا لا يوجد شيء، احسب حتى الآن
	from django.utils import timezone
	end = timezone.now()
	days = (end.date() - start.date()).days + 1
	if days < 0:
		return None
	return days


def derive_car_status(car):
	"""Derive a canonical status for a car based on the latest non-delivered MaintenanceRecord.

	Returns one of: 'waiting', 'in_progress', 'pending_payment', 'ready', 'done'.
	"""
	from django.db.models import Sum
	# latest non-delivered record
	last = car.maintenance_records.filter(delivery_date__isnull=True).order_by('-created_at').first()
	if last:
		# compute remaining amount if linked invoice exists
		inv = getattr(last, 'invoice', None)
		remaining = None
		if inv:
			try:
				paid = inv.payments.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
				remaining = float(inv.amount or 0) - float(paid or 0)
			except Exception:
				remaining = None
		# rules
		if last.is_finished:
			if remaining is None:
				return 'ready'
			if remaining > 0:
				return 'pending_payment'
			return 'ready'
		else:
			return 'in_progress'
	# no non-delivered records -> if any delivered exists -> done
	if car.maintenance_records.filter(delivery_date__isnull=False).exists():
		return 'done'
	return 'waiting'

def cars_ajax_filter(request):
	status = request.GET.get('status')
	from .maintenance_models import MaintenanceRecord
	from django.db.models import Sum

	# use shared derive_car_status defined above
	# New status semantics: waiting, in_progress, pending_payment, done
	# We'll derive status per-car from maintenance records (authoritative source)
	all_cars_qs = Car.objects.all().order_by('-created_at')
	cars = []
	def _matches_done_by_dashboard(car):
		# dashboard considers a car 'done' when it has at least one maintenance record,
		# no active (unfinished) maintenance records, and no unpaid invoices.
		try:
			has_mrs = car.maintenance_records.exists()
			has_unfinished = car.maintenance_records.filter(is_finished=False).exists()
			has_unpaid = car.invoices.filter(paid=False).exists()
			return has_mrs and (not has_unfinished) and (not has_unpaid)
		except Exception:
			return False

	if status in ('waiting', 'in_progress', 'pending_payment', 'done', 'ready'):
		# derive status per-car to keep semantics consistent with maintenance records
		for car in all_cars_qs:
			st = derive_car_status(car)
			# Include car only when derived status matches. For 'done' also accept
			# cars that match the dashboard definition (no unfinished maintenance
			# and no unpaid invoices). This avoids duplicate inclusion across
			# multiple filter buckets when DB `Car.status` may be stale.
			if st == status or (status == 'done' and _matches_done_by_dashboard(car)):
				cars.append(car)
	elif status == 'paid_waiting_collection':
		# keep existing semantic: cars with paid invoices waiting collection
		cars = list(Car.objects.filter(status='paid_waiting_collection').order_by('-created_at'))
	else:
		cars = []
	# حساب مدة العمل وتمريرها للقالب
	cars = list(cars)
	for car in cars:
		# attach derived status for template usage
		try:
			car.derived_status = derive_car_status(car)
		except Exception:
			car.derived_status = getattr(car, 'status', None)
		start, end = get_work_duration_dates(car)
		car.work_start = start
		car.work_end = end
		car.work_days = get_work_duration_days(car)
	# جلب أرقام هواتف جميع العملاء المسجلين
	from clients.models import Client
	from bookings.models import Booking
	existing_phones = set(Client.objects.values_list('phone_number', flat=True))
	# بناء قاموس يحوي قائمة الحجوزات لكل رقم هاتف
	bookings_per_phone = {}
	for phone in existing_phones:
		bookings_per_phone[phone] = list(Booking.objects.filter(phone=phone).order_by('-service_date'))
	# تمرير القاموس للقالب
	print(f"[DEBUG] فلتر: {status} - عدد السيارات: {len(cars)}")
	html = render_to_string('cars_list_partial.html', {
		'cars': cars,
		'existing_phones': existing_phones,
		'bookings_per_phone': bookings_per_phone,
		'ajax': True
	}, request=request)
	return HttpResponse(html)

from .models import Car
@login_required
def cars_list(request):
	plate_number = request.GET.get('plate_number')
	status = request.GET.get('status')
	cars_qs = Car.objects.all()
	# If the requested status is one of the derived statuses, we must filter
	# by the derived logic (latest non-delivered MaintenanceRecord). For
	# other statuses (including paid_waiting_collection) keep DB filtering.
	derived_statuses = ('waiting', 'in_progress', 'pending_payment', 'done', 'ready')
	if status:
		if status in derived_statuses:
			# leave cars_qs as all and apply derived filtering after evaluating queryset
			pass
		else:
			cars_qs = cars_qs.filter(status=status)
	if plate_number:
		cars_qs = cars_qs.filter(plate_number__icontains=plate_number)
	# handle per-page pagination like inventory
	per_page_options = [25,50,100,200,'all']
	per_page = request.GET.get('per_page')
	if per_page is None:
		per_page = request.session.get('cars_per_page', 25)
	if str(per_page) == 'all':
		per_page_val = 0
	else:
		try:
			per_page_val = int(per_page)
		except Exception:
			per_page_val = 25

	# evaluate queryset to list for stable ordering
	cars_list = list(cars_qs.order_by('-created_at'))

	# If filtering by a derived status, compute the filtered list here so
	# the page matches the AJAX/dashboard semantics.
	if status in derived_statuses:
		all_cars = list(Car.objects.all().order_by('-created_at'))
		# compatibility: match either derived status or DB status so older workflows still appear
		# additionally for 'done' include cars meeting dashboard 'done' criteria
		if status == 'done':
			cars_list = [c for c in all_cars if derive_car_status(c) == status or _matches_done_by_dashboard(c)]
		else:
			cars_list = [c for c in all_cars if derive_car_status(c) == status]
	elif status == 'paid_waiting_collection':
		cars_list = list(Car.objects.filter(status='paid_waiting_collection').order_by('-created_at'))

	page_obj = None
	paginator = None
	cars = cars_list
	if per_page_val > 0:
		from django.core.paginator import Paginator, EmptyPage
		paginator = Paginator(cars_list, per_page_val)
		try:
			page_number = int(request.GET.get('page', 1))
		except Exception:
			page_number = 1
		try:
			page_obj = paginator.page(page_number)
			cars = page_obj.object_list
		except EmptyPage:
			page_obj = paginator.page(paginator.num_pages)
			cars = page_obj.object_list
	else:
		# show all
		cars = cars_list

	# attach derived status for template usage (keeps page in sync with derived semantics)
	for car in cars:
		try:
			car.derived_status = derive_car_status(car)
		except Exception:
			car.derived_status = getattr(car, 'status', None)

	# persist per_page in session
	try:
		request.session['cars_per_page'] = per_page if per_page_val != 0 else 'all'
	except Exception:
		pass

	context = {'cars': cars, 'per_page': (0 if per_page_val==0 else per_page_val), 'per_page_options': per_page_options, 'page_obj': page_obj, 'paginator': paginator, 'plate_number': plate_number, 'status': status}
	return render(request, 'cars_list.html', context)


@_login_required
@_require_POST
def change_status(request, car_id):
	"""Change the DB `Car.status` from the cars list page (staff action)."""
	car = get_object_or_404(Car, id=car_id)
	new_status = request.POST.get('new_status')
	allowed = {'waiting', 'in_progress', 'pending_payment', 'paid_waiting_collection', 'done'}
	if new_status in allowed:
		car.status = new_status
		car.save()
	return redirect(f"/cars/?plate_number={car.plate_number}")

@login_required
def maintenance_list(request):
	from .maintenance_models import MaintenanceRecord
	plate_number = request.GET.get('plate_number', '').strip()
	qs = MaintenanceRecord.objects.select_related('car', 'service', 'invoice').order_by('-created_at')
	if plate_number:
		qs = qs.filter(car__plate_number__icontains=plate_number)
	# Pagination / per-page handling (match other lists)
	per_page_options = [25,50,100,200,'all']
	per_page_raw = request.GET.get('per_page')
	if per_page_raw is None:
		per_page = request.session.get('maintenance_per_page', 25)
	else:
		if str(per_page_raw).lower() in ('all','0','none'):
			per_page = 0
		else:
			try:
				per_page = int(per_page_raw)
			except Exception:
				per_page = 25
		# persist
		try:
			request.session['maintenance_per_page'] = per_page
		except Exception:
			pass
	# apply pagination
	page_obj = None
	paginator = None
	records = None
	if per_page and int(per_page) > 0:
		from django.core.paginator import Paginator, EmptyPage
		paginator = Paginator(qs, per_page)
		try:
			page_number = int(request.GET.get('page', 1))
		except Exception:
			page_number = 1
		try:
			page_obj = paginator.page(page_number)
			records = page_obj.object_list
		except EmptyPage:
			page_obj = paginator.page(paginator.num_pages)
			records = page_obj.object_list
	else:
		# show all
		records = list(qs)

	context = {
		'records': records,
		'plate_number': plate_number,
		'per_page': (0 if str(per_page)== '0' or per_page==0 else per_page),
		'per_page_options': per_page_options,
		'page_obj': page_obj,
		'paginator': paginator,
	}
	return render(request, 'maintenance_list.html', context)

# تعديل سجل صيانة
from .maintenance_models import MaintenanceRecord
from .forms_maintenance import MaintenanceRecordForm
from django.shortcuts import get_object_or_404, redirect
def edit_maintenance_record(request, record_id):
	record = get_object_or_404(MaintenanceRecord, id=record_id)
	if request.method == 'POST':
		form = MaintenanceRecordForm(request.POST)
		if form.is_valid():
			print("SERVICE VALUE:", form.cleaned_data['service'], type(form.cleaned_data['service']))
			record.service = form.cleaned_data['service']
			record.price = form.cleaned_data['price']
			record.notes = form.cleaned_data['notes']
			record.save()
			return redirect('maintenance_list')
	else:
		form = MaintenanceRecordForm(initial={
			'service': record.service,
			'price': record.price,
			'notes': record.notes,
		})
	return render(request, 'edit_maintenance_record.html', {'form': form, 'record': record})


@require_POST
def finish_maintenance_record(request, record_id):
	from django.utils import timezone
	record = get_object_or_404(MaintenanceRecord, id=record_id)
	if not record.is_finished:
		record.is_finished = True
		record.ready_at = timezone.now()
		record.save()
	# if all records for this car are finished, move car to pending_payment
	car = record.car
	if not car.maintenance_records.filter(is_finished=False).exists():
		car.status = 'pending_payment'
		car.save()
	return redirect('cars:maintenance_list')

# حذف سجل صيانة
def delete_maintenance_record(request, record_id):
	record = get_object_or_404(MaintenanceRecord, id=record_id)
	if request.method == 'POST':
		car = record.car
		record.delete()
		# إذا لم يبق أي سجل صيانة للسيارة، أعد الحالة إلى 'active'
		if not car.maintenance_records.exists():
			car.status = 'waiting'
			car.save()
		return redirect('cars:maintenance_list')
	return render(request, 'delete_maintenance_record.html', {'record': record})



# إنهاء الصيانة (تحويل السيارة إلى ready)
@require_POST
def finish_maintenance(request, car_id):
	car = get_object_or_404(Car, id=car_id)
	try:
		with open('debug_finish.log', 'a', encoding='utf-8') as _f:
			_f.write(f"FINISH_CALLED: car_id={car_id} user={getattr(request.user,'id',None)}\n")
	except Exception:
		pass
	from cars.maintenance_models import MaintenanceRecord
	# Mark all maintenance records as finished for this car and set ready timestamp
	from django.utils import timezone
	MaintenanceRecord.objects.filter(car=car, is_finished=False).update(is_finished=True, ready_at=timezone.now())
	# Check if all maintenance records are finished
	all_finished = not car.maintenance_records.filter(is_finished=False).exists()
	if all_finished:
		# transition to pending_payment and create invoice if none unpaid
		car.status = 'pending_payment'
		car.save()
		from invoices.models import Invoice
		if not car.invoices.filter(paid=False).exists():
			from django.utils import timezone
			invoice_number = f"INV-{car.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
			amount = 0
			for rec in car.maintenance_records.filter(invoice__isnull=True):
				amount += rec.price
			invoice = Invoice.objects.create(
				invoice_number=invoice_number,
				client=car.client,
				car=car,
				amount=amount,
				paid=False
			)
			for rec in car.maintenance_records.filter(invoice__isnull=True):
				rec.invoice = invoice
				rec.save()
	else:
		# keep in_progress if not all finished
		if car.status != 'in_progress':
			car.status = 'in_progress'
			car.save()
	# بعد إنهاء الصيانة، أعِد التوجيه إلى لوحة التحكم
	return redirect('/dashboard/')

# توصيل السيارة (تحويل السيارة إلى pending_payment)
from django.views.decorators.http import require_POST
@require_POST
def deliver_car(request, car_id):
	car = get_object_or_404(Car, id=car_id)
	# Allow forcing status during local testing when DEBUG=True.
	from django.conf import settings
	force_status = None
	if settings.DEBUG:
		force_status = request.POST.get('force_status') or request.GET.get('force_status')
		if force_status:
			allowed = {'waiting', 'in_progress', 'pending_payment', 'paid_waiting_collection', 'ready', 'done'}
			if force_status not in allowed:
				force_status = None

	# Determine or create invoice as needed, but decide final car.status based on
	# whether there are unpaid invoices or only paid invoices.
	from invoices.models import Invoice
	unpaid_invoice = car.invoices.filter(paid=False).first()
	if unpaid_invoice is None:
		# create a new unpaid invoice if there are maintenance records without an invoice
		from django.utils import timezone
		invoice_number = f"INV-{car.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
		amount = 0
		for rec in car.maintenance_records.filter(invoice__isnull=True):
			amount += rec.price
		# Only create an invoice when there's a real amount to bill
		if amount > 0:
			invoice = Invoice.objects.create(
				invoice_number=invoice_number,
				client=car.client,
				car=car,
				amount=amount,
				paid=False
			)
			for rec in car.maintenance_records.filter(invoice__isnull=True):
				rec.invoice = invoice
				rec.save()
			unpaid_invoice = invoice

	# Decide resulting status:
	# If a force_status was provided (local DEBUG testing), apply it and skip
	# invoice-driven determination so tests can simulate workflows.
	if force_status:
		car.status = force_status
		car.save()
	else:
		has_unpaid = car.invoices.filter(paid=False).exists()
		has_paid = car.invoices.filter(paid=True).exists()
		if has_unpaid:
			car.status = 'pending_payment'
		elif has_paid and not has_unpaid:
			car.status = 'paid_waiting_collection'
		else:
			# fallback: pending_payment to surface billing flow
			car.status = 'pending_payment'
		car.save()
	# لا حاجة لتعيين unpaid_invoice_id لأنه property
	# تحديث تاريخ تسليم المركبة في سجل الصيانة غير المسلم
	from cars.maintenance_models import MaintenanceRecord
	record_to_deliver = MaintenanceRecord.objects.filter(car=car, delivery_date__isnull=True).order_by('-created_at').first()
	if record_to_deliver:
		from django.utils import timezone
		from django.db import transaction
		now = timezone.now()
		try:
			with transaction.atomic():
				record_to_deliver.delivery_date = now
				record_to_deliver.save()
				# Update car status to done so DB filters reflect the delivered state
				car.status = 'done'
				car.save()
		except Exception:
			# best-effort fallback in case atomic update fails
			try:
				record_to_deliver.delivery_date = now
				record_to_deliver.save()
			except Exception:
				pass
			car.status = 'done'
			car.save()
	# بعد التسليم، أعد التوجيه إلى لوحة التحكم
	return redirect('/dashboard/')


# During local development allow POSTing to deliver without CSRF so the smoke
# test can exercise the DEBUG-only `force_status` hook. This is intentionally
# enabled only when DEBUG=True.
from django.views.decorators.csrf import csrf_exempt
import os, time
from django.conf import settings as _dj_settings

# Enable CSRF exemption only when DEBUG=True and a toggle file exists and
# its modification time is within the allowed window (1 hour). This allows
# temporary test enabling without committing code changes.
try:
	toggle_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.csrf_exempt_toggle')
	if getattr(_dj_settings, 'DEBUG', False) and os.path.exists(toggle_path):
		mtime = os.path.getmtime(toggle_path)
		if time.time() - mtime < 3600:
			deliver_car = csrf_exempt(deliver_car)
except Exception:
	pass


# تعيين السيارة كمستلمة (تم جمعها) — ضبط تواريخ التسليم والحالة إلى 'done'
@require_POST
def mark_collected(request, car_id):
	from django.utils import timezone
	from django.db import transaction
	car = get_object_or_404(Car, id=car_id)
	# Atomically update delivery_date for any maintenance record without delivery_date
	from .maintenance_models import MaintenanceRecord
	now = timezone.now()
	try:
		with transaction.atomic():
			MaintenanceRecord.objects.filter(car=car, delivery_date__isnull=True).update(delivery_date=now)
			# Update car status to done in DB so filters/options reflect collection
			car.status = 'done'
			car.save()
	except Exception:
		# best-effort fallback: update individually if atomic block fails
		for rec in MaintenanceRecord.objects.filter(car=car, delivery_date__isnull=True):
			rec.delivery_date = now
			rec.save()
		car.status = 'done'
		car.save()
	return redirect('/dashboard/')

# بدء الصيانة
@require_POST
def start_maintenance(request, car_id):
	car = get_object_or_404(Car, id=car_id)
	# جلب جميع سجلات الصيانة المرتبطة بالسيارة
	maintenance_records = list(car.maintenance_records.all().order_by('created_at'))
	# مثال: طباعة عدد سجلات الصيانة لهذه السيارة
	print(f"عدد سجلات الصيانة للسيارة {car.plate_number}: {len(maintenance_records)}")
	if car.status == 'waiting':
		car.status = 'in_progress'
		car.save()
	# بعد بدء التنفيذ، أعد التوجيه إلى فلتر "جاري التنفيذ"
	return redirect('/cars/?status=in_progress')
