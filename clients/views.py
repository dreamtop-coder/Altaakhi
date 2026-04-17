
from django.shortcuts import render, redirect, get_object_or_404
from .models import Client
from cars.models import Car
from invoices.models import Payment
from .forms import ClientForm
from django.db.models import Q, Sum
from invoices.models import Invoice, Payment
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.views.decorators.http import require_GET

def clients_list(request):
	search = request.GET.get('search', '').strip()
	clients_qs = Client.objects.all()
	cars_matched_by_search = {}  # client_id -> list of matched plate_numbers
	if search:
		normalized_search = search.replace(' ', '').upper()
		# البحث في جميع الحقول كما هو
		car_ids = [car.client_id for car in Car.objects.all() if car.plate_number and normalized_search in car.plate_number.replace(' ', '').upper()]
		clients_qs = Client.objects.filter(
			Q(first_name__icontains=search) |
			Q(last_name__icontains=search) |
			Q(customer_id__icontains=search) |
			Q(phone_number__icontains=search) |
			Q(id__in=car_ids)
		).distinct()
		# تجهيز قائمة أرقام السيارات المطابقة لكل عميل (للاستخدام في القالب)
		for client in clients_qs:
			matched_plates = [car.plate_number for car in client.cars.all() if car.plate_number and normalized_search in car.plate_number.replace(' ', '').upper()]
			if matched_plates:
				cars_matched_by_search[client.id] = matched_plates
	clients_qs = clients_qs.order_by('id')
	# Debug prints removed for production

	# --- Pagination / per_page handling ---
	# supported per-page options (integer or 0 for 'all')
	PER_PAGE_DEFAULT = 25
	per_page_raw = request.GET.get('per_page')
	if per_page_raw is None:
		# try session
		per_page = request.session.get('clients_per_page', PER_PAGE_DEFAULT)
	else:
		if str(per_page_raw).lower() in ('all', '0', 'none'):
			per_page = 0
		else:
			try:
				per_page = int(per_page_raw)
			except Exception:
				per_page = PER_PAGE_DEFAULT
		# persist choice in session
		request.session['clients_per_page'] = per_page

	page_number = request.GET.get('page', 1)
	clients = None
	page_obj = None
	paginator = None
	if per_page and int(per_page) > 0:
		paginator = Paginator(clients_qs, per_page)
		try:
			page_obj = paginator.get_page(page_number)
		except (PageNotAnInteger, EmptyPage):
			page_obj = paginator.get_page(1)
		clients = page_obj.object_list
	else:
		# per_page == 0 means show all
		clients = list(clients_qs)
		page_obj = None
	# Compute invoiced and paid amounts for the returned clients (current page or all)
	client_ids = [c.id for c in clients]
	invoices_sum_qs = Invoice.objects.filter(client_id__in=client_ids).values('client_id').annotate(total_invoiced=Sum('amount'))
	payments_sum_qs = Payment.objects.filter(client_id__in=client_ids).values('client_id').annotate(total_paid=Sum('amount'))
	invoiced_map = {item['client_id']: item['total_invoiced'] or 0 for item in invoices_sum_qs}
	paid_map = {item['client_id']: item['total_paid'] or 0 for item in payments_sum_qs}
	amounts_by_client = {}
	for cid in client_ids:
		total_invoiced = invoiced_map.get(cid, 0)
		total_paid = paid_map.get(cid, 0)
		amounts_by_client[cid] = {
			'invoiced': total_invoiced,
			'paid': total_paid,
			'remaining': (total_invoiced or 0) - (total_paid or 0)
		}
	ctx = {
		'clients': clients,
		'search': search,
		'cars_matched_by_search': cars_matched_by_search,
		'amounts_by_client': amounts_by_client,
		'per_page': per_page,
		'per_page_options': [25,50,100,200,'all'],
		'page_obj': page_obj,
		'paginator': paginator,
	}
	return render(request, 'clients_list.html', ctx)


@require_POST
def bulk_delete_clients(request):
	ids = request.POST.getlist('client_ids[]') or request.POST.getlist('client_ids')
	if ids:
		Client.objects.filter(id__in=ids).delete()
	return redirect('clients_list')


def clients_print(request):
	ids = request.GET.get('ids', '')
	id_list = [int(x) for x in ids.split(',') if x.strip().isdigit()]
	clients_qs = Client.objects.filter(id__in=id_list)
	return render(request, 'clients_print.html', {'clients': clients_qs})

def add_client(request):
	if request.method == 'POST':
		form = ClientForm(request.POST)
		if form.is_valid():
			client = form.save(commit=False)
			if not client.created_at:
				from django.utils import timezone
				client.created_at = timezone.now()
			client.save()
			return redirect('client_detail', client_id=client.id)
	else:
		# جلب رقم الهاتف من باراميتر البحث إن وجد
		phone_number = request.GET.get('search', '').strip()
		initial = {'phone_number': phone_number} if phone_number else None
		form = ClientForm(initial=initial)
	return render(request, 'clients/add_client.html', {'form': form})

def delete_client(request, client_id):
	client = get_object_or_404(Client, id=client_id)
	if request.method == 'POST':
		client.delete()
		return redirect('clients_list')
	return render(request, 'clients/delete_client.html', {'client': client})


def client_detail(request, client_id):
	client = get_object_or_404(Client, id=client_id)
	cars = client.cars.all()
	# لكل مركبة: جلب سجلات الصيانة والفواتير
	cars_data = []
	for car in cars:
		maintenance_records = car.maintenance_records.select_related('invoice', 'service').all().order_by('-created_at')
		records_with_payments = []
		for record in maintenance_records:
			payment_dates = []
			if record.invoice:
				payments = record.invoice.payments.filter(status='paid').order_by('payment_date')
				payment_dates = [p.payment_date for p in payments]
			records_with_payments.append({
				'record': record,
				'payment_dates': payment_dates
			})
		# إضافة has_unpaid_invoice لكل مركبة
		has_unpaid_invoice = car.invoices.filter(paid=False).exists()
		cars_data.append({
			'car': car,
			'maintenance_records': records_with_payments,
			'has_unpaid_invoice': has_unpaid_invoice,
		})
	return render(request, 'client_detail.html', {
		'client': client,
		'cars_data': cars_data,
	})

def edit_client(request, client_id):
	client = get_object_or_404(Client, id=client_id)
	if request.method == 'POST':
		form = ClientForm(request.POST, instance=client)
		if form.is_valid():
			form.save()
			return redirect('clients_list')
	else:
		form = ClientForm(instance=client)
	return render(request, 'clients/edit_client.html', {
		'form': form,
		'client': client
	})


@require_GET
def search_clients_api(request):
	q = request.GET.get('q', '').strip()
	results = []
	if q:
		qs = Client.objects.filter(
			Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(phone_number__icontains=q) | Q(cars__plate_number__icontains=q)
		).distinct()[:50]
	else:
		qs = Client.objects.all().order_by('-id')[:50]
	for c in qs:
		plates = [car.plate_number for car in c.cars.all()[:5] if car.plate_number]
		cars_list = []
		for car in c.cars.all()[:20]:
			if not car.plate_number:
				continue
			brand = car.brand.name if getattr(car, 'brand', None) else ''
			model = car.model.name if getattr(car, 'model', None) else ''
			cars_list.append({'id': car.id, 'plate': car.plate_number, 'brand': brand, 'model': model})
		results.append({'id': c.id, 'name': f"{c.first_name} {c.last_name or ''}".strip(), 'phone': getattr(c, 'phone_number', ''), 'plates': plates, 'cars': cars_list})
	return JsonResponse({'results': results})


