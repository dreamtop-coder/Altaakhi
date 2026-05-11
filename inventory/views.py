from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.db.models.functions import Length
from django.db.models import IntegerField
from django.db.models.functions import Cast, Substr
from .models import Supplier, Part
from .forms import SupplierForm, PartForm
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q


def suppliers_list(request):
	"""Simple suppliers listing page."""
	suppliers_qs = Supplier.objects.all().order_by('name')

	# per-page pagination handling (match clients list behavior)
	PER_PAGE_DEFAULT = 25
	per_page_raw = request.GET.get('per_page')
	# normalize incoming value and prefer clients preference when not specified
	if per_page_raw is None:
		stored = request.session.get('suppliers_per_page', request.session.get('clients_per_page', PER_PAGE_DEFAULT))
		per_page_raw = stored

	# interpret values: 'all' -> 0, numeric -> int
	per_page_val = None
	if isinstance(per_page_raw, str) and per_page_raw.lower() in ('all', '0', 'none'):
		per_page_val = 0
	else:
		try:
			per_page_val = int(per_page_raw)
		except Exception:
			per_page_val = PER_PAGE_DEFAULT

	# persist user's preference in session
	try:
		request.session['suppliers_per_page'] = ('all' if per_page_val == 0 else per_page_val)
	except Exception:
		pass

	page_number = request.GET.get('page', 1)
	suppliers = []
	page_obj = None
	paginator = None
	if per_page_val and int(per_page_val) > 0:
		paginator = Paginator(suppliers_qs, per_page_val)
		try:
			page_obj = paginator.get_page(page_number)
		except Exception:
			page_obj = paginator.get_page(1)
		suppliers = page_obj.object_list
	else:
		# show all
		suppliers = list(suppliers_qs)

	context = {
		'suppliers': suppliers,
		'per_page': (0 if per_page_val == 0 else int(per_page_val)),
		'per_page_options': [25,50,100,200,'all'],
		'page_obj': page_obj,
		'paginator': paginator,
	}

	return render(request, 'suppliers_list.html', context)


def add_supplier(request):
	if request.method == 'POST':
		form = SupplierForm(request.POST)
		if form.is_valid():
			form.save()
			return redirect('suppliers_list')
	else:
		form = SupplierForm()
	return render(request, 'supplier_form.html', {'form': form, 'title': 'Add Supplier'})


def edit_supplier(request, supplier_id):
	try:
		s = Supplier.objects.get(pk=supplier_id)
	except Supplier.DoesNotExist:
		return redirect('suppliers_list')
	if request.method == 'POST':
		form = SupplierForm(request.POST, instance=s)
		if form.is_valid():
			form.save()
			return redirect('suppliers_list')
	else:
		form = SupplierForm(instance=s)
	return render(request, 'supplier_form.html', {'form': form, 'title': 'Edit Supplier'})


def delete_supplier(request, supplier_id):
	try:
		s = Supplier.objects.get(pk=supplier_id)
		s.delete()
	except Supplier.DoesNotExist:
		pass
	return redirect('suppliers_list')


def inventory_list(request):
	"""List parts (inventory)."""
	q = request.GET.get('q', '').strip()
	# support sentinel from frontend to request defaults
	if q == '__ALL__':
		q = ''
	# allow frontend to request a full/default list using a sentinel token
	if q == '__ALL__':
		q = ''

	# Order by code length then code so shorter codes (e.g. 001) come before longer (e.g. 0001)
	parts_qs = Part.objects.annotate(
		code_length=Length('code')
	).order_by('code_length', 'code')

	if q:
		parts_qs = parts_qs.filter(name__icontains=q)

	# handle per-page pagination (optional)
	per_page_options = [25, 50, 100, 200, 'all']
	per_page = request.GET.get('per_page')
	if per_page is None:
		per_page = request.session.get('inventory_per_page', 25)
	if str(per_page) == 'all':
		per_page_val = 0
	else:
		try:
			per_page_val = int(per_page)
		except Exception:
			per_page_val = 25

	# evaluate queryset to concrete list to preserve ordering in template
	parts_list = list(parts_qs)
	server_codes = ','.join([p.code or '' for p in parts_list])
	debug_codes = None
	if request.GET.get('debug'):
		debug_codes = server_codes

	page_obj = None
	paginator = None
	parts = parts_list
	if per_page_val > 0:
		from django.core.paginator import Paginator, EmptyPage
		paginator = Paginator(parts_list, per_page_val)
		try:
			page_number = int(request.GET.get('page', 1))
		except Exception:
			page_number = 1
		try:
			page_obj = paginator.page(page_number)
			parts = page_obj.object_list
		except EmptyPage:
			page_obj = paginator.page(paginator.num_pages)
			parts = page_obj.object_list
	else:
		# 'all' selected
		parts = parts_list

	# persist per_page in session
	try:
		request.session['inventory_per_page'] = per_page if per_page_val != 0 else 'all'
	except Exception:
		pass

	context = {'parts': parts, 'query': q, 'debug_codes': debug_codes, 'server_codes': server_codes, 'per_page': (0 if per_page_val==0 else per_page_val), 'per_page_options': per_page_options, 'page_obj': page_obj, 'paginator': paginator}
	html = render_to_string('inventory.html', context, request=request)
	try:
		# remove any <form>...</form> blocks that contain the legacy search input
		import re
		def _strip_search_form(match):
			block = match.group(0).lower()
			if 'name="q"' in block or 'placeholder="search parts"' in block or 'placeholder="بحث' in block:
				return ''
			return match.group(0)
		html = re.sub(r'<form\b[^>]*>.*?<\/form>', _strip_search_form, html, flags=re.IGNORECASE|re.DOTALL)
	except Exception:
		pass
	return HttpResponse(html)


def add_part(request):
	if request.method == 'POST':
		form = PartForm(request.POST)
		if form.is_valid():
			form.save()
			return redirect('inventory')
	else:
		form = PartForm()
	return render(request, 'part_form.html', {'form': form, 'title': 'Add Part'})


def edit_part(request, part_id):
	try:
		part = Part.objects.get(pk=part_id)
	except Part.DoesNotExist:
		return redirect('inventory')
	if request.method == 'POST':
		form = PartForm(request.POST, instance=part)
		if form.is_valid():
			form.save()
			return redirect('inventory')
	else:
		form = PartForm(instance=part)
	return render(request, 'part_form.html', {'form': form, 'title': 'Edit Part'})


from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json


def inventory_search_json(request):
	"""Return JSON list of parts for autocomplete (GET param: q)."""
	# support lookup by id for direct retrieval
	id_raw = request.GET.get('id')
	q = request.GET.get('q', '').strip()
	if id_raw:
		try:
			p = Part.objects.get(pk=int(id_raw))
			result = {
				'id': p.id,
				'name': p.name,
				'code': p.code or '',
				'sale_price': str(p.sale_price),
				'purchase_price': str(p.purchase_price),
				'quantity': p.quantity,
				'track_stock': bool(p.track_stock),
			}
			return JsonResponse({'results': [result]})
		except Exception:
			return JsonResponse({'results': []})
	# Use a limited, efficient QuerySet and return only required fields.
	# If a query was provided, search by name/code; otherwise return
	# a sensible default list (recent parts) so the autocomplete shows
	# useful suggestions on focus/click with an empty query.
	# Support explicit `all=1` param for clients that request the full/default list.
	results = []
	try:
		if request.GET.get('all') == '1' or not q:
			parts_vals = list(Part.objects.all().order_by('-id').values('id', 'name', 'code', 'sale_price', 'purchase_price', 'quantity', 'track_stock')[:50])
		else:
			parts_vals = list(Part.objects.all().order_by('code').filter(Q(name__icontains=q) | Q(code__icontains=q)).values('id', 'name', 'code', 'sale_price', 'purchase_price', 'quantity', 'track_stock')[:50])
		for p in parts_vals:
			results.append({
				'id': p.get('id'),
				'name': p.get('name') or '',
				'code': p.get('code') or '',
				'sale_price': str(p.get('sale_price')) if p.get('sale_price') is not None else None,
				'purchase_price': str(p.get('purchase_price')) if p.get('purchase_price') is not None else None,
				'quantity': p.get('quantity'),
				'stock': p.get('quantity'),
				'track_stock': bool(p.get('track_stock')),
			})
	except Exception:
		results = []
	return JsonResponse({'results': results})


def suppliers_search_json(request):
	"""Return JSON list of suppliers for autocomplete (GET param: q)."""
	# support lookup by id for direct retrieval
	id_raw = request.GET.get('id')
	q = request.GET.get('q', '').strip()
	if id_raw:
		try:
			s = Supplier.objects.get(pk=int(id_raw))
			result = {
				'id': s.id,
				'name': s.name,
				'phone': s.phone or '',
				'email': s.email or '',
				'address': s.address or '',
			}
			return JsonResponse({'results': [result]})
		except Exception:
			return JsonResponse({'results': []})

	suppliers_qs = Supplier.objects.all().order_by('name')
	if q:
		suppliers_qs = suppliers_qs.filter(Q(name__icontains=q) | Q(phone__icontains=q))

	suppliers = suppliers_qs[:100]
	results = []
	for s in suppliers:
		results.append({
			'id': s.id,
			'name': s.name,
			'phone': s.phone or '',
			'email': s.email or '',
			'address': s.address or '',
		})
	return JsonResponse({'results': results})


@require_POST
def inventory_bulk_delete(request):
	try:
		data = json.loads(request.body.decode('utf-8'))
		ids = data.get('ids', [])
	except Exception:
		return JsonResponse({'ok': False, 'error': 'Invalid request'}, status=400)
	if not isinstance(ids, list):
		return JsonResponse({'ok': False, 'error': 'Invalid ids'}, status=400)
	deleted = 0
	for _id in ids:
		try:
			p = Part.objects.get(pk=int(_id))
			p.delete()
			deleted += 1
		except Exception:
			continue
	return JsonResponse({'ok': True, 'deleted': deleted})
