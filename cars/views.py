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
	# Compute counts based on derived status so UI reflects maintenance records
	done_count = 0
	paid_waiting_count = 0
	try:
		all_cars = Car.objects.all()
		for c in all_cars:
			try:
				st = derive_car_status(c)
			except Exception:
				st = getattr(c, 'status', None)
			if st == 'done':
				done_count += 1
			# keep paid_waiting_count compatible with DB semantic for this badge
			if getattr(c, 'status', None) == 'paid_waiting_collection' or st == 'paid_waiting_collection':
				paid_waiting_count += 1
	except Exception:
		# fallback to DB counts if something goes wrong
		done_count = Car.objects.filter(status='done').count()
		paid_waiting_count = Car.objects.filter(status='paid_waiting_collection').count()
	return JsonResponse({'done_count': done_count, 'paid_waiting_count': paid_waiting_count})
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
			messages.success(request, 'Maintenance record updated successfully.')
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
	Compute start and end datetimes for a car's actual work duration.
	"""
	# Prefer computing duration for the most recent job (invoice-linked records)
	from django.utils import timezone
	from cars.maintenance_models import MaintenanceRecord
	# all maintenance records ordered by created_at
	all_records_qs = MaintenanceRecord.objects.filter(car=car).order_by('created_at')
	if not all_records_qs.exists():
		return None, None
	# If there's a recent invoice, prefer the maintenance records tied to that invoice
	latest_invoice = car.invoices.order_by('-created_at').first()
	if latest_invoice:
		recs_for_inv = list(all_records_qs.filter(invoice=latest_invoice).order_by('created_at'))
		if recs_for_inv:
			start = recs_for_inv[0].created_at
			# prefer last payment date when available
			try:
				last_payment = latest_invoice.payments.filter(status='paid').order_by('-payment_date').first()
				if last_payment and getattr(last_payment, 'payment_date', None):
					end = last_payment.payment_date
				else:
					end = latest_invoice.created_at or recs_for_inv[-1].created_at
			except Exception:
				end = latest_invoice.created_at or recs_for_inv[-1].created_at
			return start, end
	# Fallback: use first maintenance as start and prefer last paid invoice/payment or last finished record
	first_rec = all_records_qs.first()
	start = first_rec.created_at
	paid_invoices = car.invoices.filter(paid=True).order_by('-created_at')
	if paid_invoices.exists():
		last_paid = paid_invoices.first()
		last_payment = last_paid.payments.filter(status='paid').order_by('-payment_date').first()
		if last_payment and getattr(last_payment, 'payment_date', None):
			end = last_payment.payment_date
			return start, end
	# use last finished maintenance record
	finished_records = list(all_records_qs.filter(is_finished=True).order_by('created_at'))
	if finished_records:
		end = finished_records[-1].created_at
		return start, end
	# otherwise use now
	return start, timezone.now()

def get_work_duration_days(car):
	"""
	Compute total work duration in days (1 day if same day, 2 if one-day diff, etc.).
	"""
	from django.utils import timezone
	from cars.maintenance_models import MaintenanceRecord
	all_records_qs = MaintenanceRecord.objects.filter(car=car).order_by('created_at')
	if not all_records_qs.exists():
		return None
	# Prefer job-scoped duration when there's a recent invoice
	latest_invoice = car.invoices.order_by('-created_at').first()
	if latest_invoice:
		recs_for_inv = all_records_qs.filter(invoice=latest_invoice).order_by('created_at')
		if recs_for_inv.exists():
			start = recs_for_inv.first().created_at
			# end is last payment date or invoice.created_at
			last_payment = latest_invoice.payments.filter(status='paid').order_by('-payment_date').first()
			if last_payment and getattr(last_payment, 'payment_date', None):
				end = last_payment.payment_date
			else:
				end = latest_invoice.created_at or recs_for_inv.last().created_at
			days = (end.date() - start.date()).days + 1
			if days < 0:
				return None
			return days
	# Fallback: use first maintenance as start and prefer last paid invoice/payment or last finished record
	first_rec = all_records_qs.first()
	start = first_rec.created_at
	paid_invoices = car.invoices.filter(paid=True).order_by('-created_at')
	if paid_invoices.exists():
		last_paid = paid_invoices.first()
		last_payment = last_paid.payments.filter(status='paid').order_by('-payment_date').first()
		if last_payment and getattr(last_payment, 'payment_date', None):
			end = last_payment.payment_date
			days = (end.date() - start.date()).days + 1
			if days < 0:
				return None
			return days
	finished_records = list(all_records_qs.filter(is_finished=True).order_by('created_at'))
	if finished_records:
		end = finished_records[-1].created_at
		days = (end.date() - start.date()).days + 1
		if days < 0:
			return None
		return days
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
	# latest non-delivered record — tie-break by PK to handle same-timestamp inserts
	# Use both created_at and id so records with identical timestamps still
	# deterministically select the newest record.
	last = car.maintenance_records.filter(delivery_date__isnull=True).order_by('-created_at', '-id').first()
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
	# Dashboard: when filtering `done`, show only the latest 6 cars to avoid page
	# bloat (user requested). Keep ordering by '-created_at' from queryset above.
	if status == 'done':
		# Sort delivered cars by their latest maintenance activity (delivery_date or created_at)
		# so recently completed work appears first even if the Car record is old.
		def _last_activity(car):
			try:
				mr = car.maintenance_records.order_by('-created_at', '-id').first()
				if not mr:
					return car.created_at
				# prefer delivery_date when available
				return mr.delivery_date or mr.created_at or car.created_at
			except Exception:
				return getattr(car, 'created_at', None)
		# sort in-place by last activity descending then limit
		cars = sorted(cars, key=_last_activity, reverse=True)
		# Limit to the most recent 6 delivered cars for compact dashboard view
		cars = cars[:6]
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
	# Choose per-page options based on device class: phones include a 5 option,
	# tablets (iPad) and desktop do not include 5 (they show 25,50,100,200,'all').
	def _is_phone(req):
		ua = (req.META.get('HTTP_USER_AGENT') or '').lower()
		# common phone identifiers — exclude iPad/tablet
		for k in ('mobile','iphone','blackberry','opera mini','windows phone'):
			if k in ua and 'ipad' not in ua and 'tablet' not in ua:
				return True
		# Android devices report 'mobile' for phones; some tablets don't include 'mobile'
		if 'android' in ua and 'mobile' in ua:
			return True
		return False

	def _is_tablet(req):
		ua = (req.META.get('HTTP_USER_AGENT') or '').lower()
		if 'ipad' in ua or 'tablet' in ua:
			return True
		# Android tablets often include 'android' but not 'mobile'
		if 'android' in ua and 'mobile' not in ua:
			return True
		return False

	# default options for non-phone (desktop + tablets)
	per_page_options = [25,50,100,200,'all']
	try:
		if _is_phone(request):
			per_page_options = [5,25,50,100,200,'all']
	except Exception:
		# fallback to conservative desktop options on detection failure
		per_page_options = [25,50,100,200,'all']
	# Determine per_page preference. Priority:
	# 1) explicit ?per_page= in URL (user action)
	# 2) session value but only if it was explicitly set by the user previously
	# 3) mobile default (5) when UA looks like a phone
	# 4) fallback default (25)
	per_page = request.GET.get('per_page')

	def _is_mobile(req):
		ua = (req.META.get('HTTP_USER_AGENT') or '').lower()
		for k in ('mobile','iphone','android','blackberry','opera mini','windows phone'):
			if k in ua:
				return True
		return False

	if per_page is None:
		# use session only if we previously saved a user preference AND it was
		# saved from the same device class (mobile/desktop). This prevents a
		# mobile auto-redirect from permanently overriding desktop preference.
		sess_val = request.session.get('cars_per_page', None)
		sess_user_flag = request.session.get('cars_per_page_user', False)
		sess_agent = request.session.get('cars_per_page_user_agent', None)
		current_is_mobile = _is_mobile(request)
		if sess_val is not None and sess_user_flag and ((sess_agent == 'mobile') == current_is_mobile):
			per_page = sess_val
		else:
			# mobile fallback default
			if current_is_mobile:
				per_page = 5
			else:
				per_page = 25
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
		# Note: template should call `car.is_in_workshop()` or use `car.derived_status`.

	# persist per_page in session ONLY when user explicitly set it via GET param
	try:
		# do not persist if this request is the automatic mobile redirect
		if 'per_page' in request.GET and 'auto_mobile' not in request.GET:
			request.session['cars_per_page'] = per_page if per_page_val != 0 else 'all'
			# mark that this was explicitly chosen by the user
			request.session['cars_per_page_user'] = True
			# record whether the user agent at the time of choosing was mobile or desktop
			request.session['cars_per_page_user_agent'] = 'mobile' if _is_mobile(request) else 'desktop'
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
	# filter for delivery status: '1' shows only records with delivery_date set
	delivered = request.GET.get('delivered')
	qs = MaintenanceRecord.objects.select_related('car', 'service', 'invoice').order_by('-created_at')
	if plate_number:
		qs = qs.filter(car__plate_number__icontains=plate_number)
	if delivered and str(delivered) in ('1','true','yes'):
		qs = qs.filter(delivery_date__isnull=False)
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
			# service is optional in edit form now; only update when provided
			svc = form.cleaned_data.get('service')
			if svc:
				record.service = svc
			record.price = form.cleaned_data['price']
			record.notes = form.cleaned_data['notes']
			# handle optional datetime fields
			try:
				ca = form.cleaned_data.get('created_at')
				if ca:
					from django.utils import timezone as _tz
					from django.utils import timezone
					if timezone.is_naive(ca):
						ca = _tz.make_aware(ca, _tz.get_current_timezone())
					record.created_at = ca
			except Exception:
				pass
			try:
				dd = form.cleaned_data.get('delivery_date')
				if dd:
					from django.utils import timezone as _tz
					from django.utils import timezone
					if timezone.is_naive(dd):
						dd = _tz.make_aware(dd, _tz.get_current_timezone())
					record.delivery_date = dd
			except Exception:
				pass
			record.save()
			return redirect('cars:maintenance_list')
	else:
		# prepare initial values, format datetimes for datetime-local widget
		initial = {
			'price': ("{:.3f}".format(record.price) if getattr(record, 'price', None) is not None else ''),
			'notes': record.notes,
		}
		try:
			# Prefer the linked invoice's created_at when present so the
			# maintenance date reflects the invoice date (historical entries).
			inv_dt = None
			try:
				if getattr(record, 'invoice', None) and getattr(record.invoice, 'created_at', None):
					inv_dt = record.invoice.created_at
			except Exception:
				inv_dt = None
			if inv_dt:
				initial['created_at'] = inv_dt.strftime('%Y-%m-%dT%H:%M')
			else:
				if getattr(record, 'created_at', None):
					initial['created_at'] = record.created_at.strftime('%Y-%m-%dT%H:%M')
		except Exception:
			pass
		try:
			if getattr(record, 'delivery_date', None):
				initial['delivery_date'] = record.delivery_date.strftime('%Y-%m-%dT%H:%M')
		except Exception:
			pass
		form = MaintenanceRecordForm(initial=initial)
	return render(request, 'edit_maintenance_record.html', {'form': form, 'record': record})


@require_POST
def finish_maintenance_record(request, record_id):
	from django.utils import timezone
	from django.utils import dateparse
	record = get_object_or_404(MaintenanceRecord, id=record_id)
	# allow optional ready_at/date from POST to support historic data entry
	ready_at_raw = request.POST.get('ready_at') or request.POST.get('date')
	ready_at = None
	if ready_at_raw:
		try:
			ready_at = dateparse.parse_datetime(ready_at_raw)
			if ready_at is None:
				d = dateparse.parse_date(ready_at_raw)
				if d:
					import datetime
					ready_at = datetime.datetime(d.year, d.month, d.day, 23, 59, 59)
		except Exception:
			ready_at = None
	if ready_at is None:
		ready_at = timezone.now()
	# make timezone-aware if naive
	try:
		from django.utils import timezone as _tz
		if timezone.is_naive(ready_at):
			ready_at = _tz.make_aware(ready_at, _tz.get_current_timezone())
	except Exception:
		pass
	if not record.is_finished:
		record.is_finished = True
		record.ready_at = ready_at
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
	from django.utils import dateparse
	# allow optional ready_at from POST (for importing historic finishes)
	ready_at_raw = request.POST.get('ready_at') or request.POST.get('date')
	ready_at = None
	if ready_at_raw:
		try:
			ready_at = dateparse.parse_datetime(ready_at_raw)
			if ready_at is None:
				d = dateparse.parse_date(ready_at_raw)
				if d:
					# set to end of day to reflect finish time if only date provided
					import datetime
					ready_at = datetime.datetime(d.year, d.month, d.day, 23, 59, 59)
		except Exception:
			ready_at = None
	if ready_at is None:
		ready_at = timezone.now()
	# make timezone-aware if naive
	try:
		from django.utils import timezone as _tz
		if timezone.is_naive(ready_at):
			ready_at = _tz.make_aware(ready_at, _tz.get_current_timezone())
	except Exception:
		pass
	MaintenanceRecord.objects.filter(car=car, is_finished=False).update(is_finished=True, ready_at=ready_at)
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
			unsent = list(car.maintenance_records.filter(invoice__isnull=True))
			for rec in unsent:
				amount += rec.price
			# Only create an invoice when there's a real amount to bill
			if amount > 0:
				invoice = Invoice.objects.create(
					invoice_number=invoice_number,
					client=car.client,
					car=car,
					amount=amount,
					paid=False,
					created_at=timezone.now(),
					type='maintenance'
				)
				for rec in unsent:
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
		from django.utils import dateparse
		from django.db import transaction
		# allow optional delivery_date from POST
		delivery_raw = request.POST.get('delivery_date') or request.POST.get('date')
		delivery_dt = None
		if delivery_raw:
			try:
				delivery_dt = dateparse.parse_datetime(delivery_raw)
				if delivery_dt is None:
					d = dateparse.parse_date(delivery_raw)
					if d:
						import datetime
						delivery_dt = datetime.datetime(d.year, d.month, d.day, 23, 59, 59)
			except Exception:
				delivery_dt = None
		if delivery_dt is None:
			# If no delivery date provided, prefer the invoice.created_at when available
			try:
				if record_to_deliver and getattr(record_to_deliver, 'invoice', None) and getattr(record_to_deliver.invoice, 'created_at', None):
					delivery_dt = record_to_deliver.invoice.created_at
				else:
					delivery_dt = timezone.now()
			except Exception:
				delivery_dt = timezone.now()
		try:
			# make timezone-aware if naive
			from django.utils import timezone as _tz
			if timezone.is_naive(delivery_dt):
				delivery_dt = _tz.make_aware(delivery_dt, _tz.get_current_timezone())
		except Exception:
			pass
		now = delivery_dt
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
			# mark car as active (available) after delivery; workflow state is
			# derived from maintenance records so the car can re-enter service
			car.status = 'active'
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
			car.status = 'active'
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
