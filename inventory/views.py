from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from .models import Supplier, Purchase, Part, PurchaseItem
from services.models import Service
from django.db import models
from .forms import SupplierForm, PurchaseForm
from decimal import Decimal
from .forms import PartForm
from django.db.utils import OperationalError


@login_required
def suppliers_list(request):
	q = request.GET.get("q", "").strip()
	qs = Supplier.objects.all()
	if q:
		qs = qs.filter(name__icontains=q)
	suppliers = qs.order_by("name")
	return render(request, "suppliers_list.html", {"suppliers": suppliers, "q": q})


@login_required
def inventory_index(request):
	"""عرض المخزون: قائمة الأصناف وحالة الكميات."""
	# Only show real stock items (exclude service-like entries)
	parts = (
		Part.objects.filter(is_stock_item=True)
		.select_related('department')
		.prefetch_related('suppliers')
		.order_by('name')
	)
	total_items = parts.count()
	low_stock = parts.filter(quantity__lte=models.F('low_stock_alert')).count()
	return render(request, "inventory_index.html", {"parts": parts, "total_items": total_items, "low_stock": low_stock})


@login_required
def supplier_detail(request, supplier_id):
	supplier = get_object_or_404(Supplier, id=supplier_id)
	message = None
	# Ensure form instances exist for rendering in all code paths
	form = SupplierForm(instance=supplier)
	pform = PurchaseForm()

	if request.method == "POST":
		if "save_supplier" in request.POST:
			form = SupplierForm(request.POST, instance=supplier)
			if form.is_valid():
				form.save()
				message = "تم حفظ بيانات المورد."
		elif "add_purchase" in request.POST:
			# handle purchase with multiple items submitted as arrays
			item_names = request.POST.getlist("item_name")
			item_qtys = request.POST.getlist("item_qty")
			item_unit_prices = request.POST.getlist("item_unit_price")
			invoice_number = request.POST.get("invoice_number", "")
			is_return = request.POST.get("is_return") == "on"
			notes = request.POST.get("notes", "")
			date = request.POST.get("date")

			# compute total
			total_amount = Decimal("0")
			items = []
			for name, qty, unit in zip(item_names, item_qtys, item_unit_prices):
				try:
					q = int(qty)
				except Exception:
					q = 0
				try:
					u = Decimal(unit) if unit else Decimal("0")
				except Exception:
					u = Decimal("0")
				line_total = (u * q)
				total_amount += line_total
				items.append({"name": name.strip(), "qty": q, "unit": u, "line_total": line_total})

			if len(items) == 0:
				message = "يرجى إضافة عنصر واحد على الأقل للفاتورة."
			else:
				purchase = Purchase.objects.create(
					supplier=supplier,
					invoice_number=invoice_number or None,
					date=date,
					amount=total_amount,
					is_return=is_return,
					notes=notes,
				)
				# save items and update part quantities
				for it in items:
					part_obj = None
					try:
						part_obj = Part.objects.filter(name__iexact=it["name"]).first()
					except Exception:
						part_obj = None
					PurchaseItem.objects.create(
						purchase=purchase,
						part=part_obj,
						part_name=it["name"],
						quantity=it["qty"],
						unit_price=it["unit"],
						total_price=it["line_total"],
					)
					if part_obj:
						if is_return:
							part_obj.quantity = max(0, part_obj.quantity - it["qty"]) 
						else:
							part_obj.quantity = part_obj.quantity + it["qty"]
						part_obj.save()
				return redirect("inventory:supplier_detail", supplier_id=supplier.id)

	try:
		purchases = supplier.purchases.order_by("-date")[:50]
	except OperationalError:
		purchases = []
		message = (message or "") + "\nمشكلة في قاعدة البيانات: جدول المشتريات مفقود. شغّل الترقيات (migrate)."
	try:
		parts = Part.objects.filter(suppliers=supplier)
	except OperationalError:
		parts = Part.objects.none()
		message = (message or "") + "\nمشكلة في قاعدة البيانات: جدول الأصناف مفقود. شغّل الترقيات (migrate)."

	return render(
		request,
		"supplier_detail.html",
		{
			"supplier": supplier,
			"form": form,
			"pform": pform,
			"purchases": purchases,
			"parts": parts,
			"message": message,
		},
	)


@login_required
def add_supplier(request):
	if request.method == "POST":
		form = SupplierForm(request.POST)
		if form.is_valid():
			supplier = form.save()
			return redirect("inventory:supplier_detail", supplier_id=supplier.id)
	else:
		form = SupplierForm()
	return render(request, "supplier_add.html", {"form": form})


@login_required
def delete_supplier(request, supplier_id):
	supplier = get_object_or_404(Supplier, id=supplier_id)
	supplier.delete()
	return redirect("inventory:suppliers_list")


@login_required
def items_list(request):
	q = request.GET.get("q", "").strip()
	qs = Part.objects.select_related('department').prefetch_related('suppliers').all()
	if q:
		qs = qs.filter(name__icontains=q)
	parts = qs.order_by('name')
	# also include services that have linked parts
	services = (
		Service.objects.filter(parts__isnull=False)
		.distinct()
		.prefetch_related('parts')
		.order_by('name')
	)
	return render(request, "items_list.html", {"parts": parts, "q": q, "services": services})


@login_required
def parts_autocomplete(request):
	q = request.GET.get("q", "").strip()
	results = []
	if q:
		qs = Part.objects.filter(name__icontains=q).order_by('name')[:15]
		results = [ {"id": p.id, "name": p.name, "quantity": p.quantity, "purchase_price": float(p.purchase_price or 0), "sale_price": float(p.sale_price or 0)} for p in qs ]
	return JsonResponse(results, safe=False)


@login_required
def add_item(request):
	if request.method == 'POST':
		form = PartForm(request.POST)
		if form.is_valid():
			form.save()
			return redirect('items_list')
	else:
		form = PartForm()
	return render(request, 'item_form.html', {'form': form, 'title': 'إضافة صنف'})


@login_required
def edit_item(request, item_id):
	item = get_object_or_404(Part, id=item_id)
	if request.method == 'POST':
		form = PartForm(request.POST, instance=item)
		if form.is_valid():
			form.save()
			return redirect('items_list')
	else:
		form = PartForm(instance=item)
	return render(request, 'item_form.html', {'form': form, 'title': 'تعديل صنف'})


@login_required
def delete_item(request, item_id):
	item = get_object_or_404(Part, id=item_id)
	item.delete()
	return redirect('items_list')


@login_required
def parts_list(request):
	"""Return JSON list of available parts (fallback when service has no linked parts)."""
	qs = Part.objects.order_by('name')[:200]
	results = [
		{
			"id": p.id,
			"name": p.name,
			"quantity": p.quantity,
			"purchase_price": float(p.purchase_price or 0),
			"sale_price": float(p.sale_price or 0),
		}
		for p in qs
	]
	return JsonResponse(results, safe=False)


@login_required
def purchases_list(request):
	"""قائمة فواتير المشتريات عبر جميع الموردين."""
	q = request.GET.get('q', '').strip()
	qs = Purchase.objects.select_related('supplier').order_by('-date')
	if q:
		qs = qs.filter(invoice_number__icontains=q)
	purchases = qs[:200]
	return render(request, 'inventory_purchases.html', {'purchases': purchases, 'q': q})



@login_required
def edit_purchase(request, purchase_id):
	purchase = get_object_or_404(Purchase, id=purchase_id)
	message = None
	if request.method == 'POST':
		invoice_number = request.POST.get('invoice_number') or None
		date = request.POST.get('date') or purchase.date
		notes = request.POST.get('notes') or ''
		new_is_return = request.POST.get('is_return') == 'on'

		# If return flag changed, adjust part quantities accordingly
		if purchase.is_return != new_is_return:
			# If switching from return->not return, we should add quantities back
			# If switching from not return->return, we should subtract quantities
			for item in purchase.items.all():
				if item.part:
					if purchase.is_return and not new_is_return:
						# previously returned, now normal -> increase stock
						item.part.quantity = item.part.quantity + item.quantity
					elif (not purchase.is_return) and new_is_return:
						# previously normal, now marked return -> decrease stock
						item.part.quantity = max(0, item.part.quantity - item.quantity)
					item.part.save()

		purchase.invoice_number = invoice_number
		purchase.date = date
		purchase.notes = notes
		purchase.is_return = new_is_return
		purchase.save()
		message = 'تم تحديث الفاتورة.'
		return redirect('inventory:purchases_list')

	return render(request, 'inventory_purchase_edit.html', {'purchase': purchase, 'message': message})


@login_required
def delete_purchase(request, purchase_id):
	purchase = get_object_or_404(Purchase, id=purchase_id)
	# Reverse quantities applied when the purchase was created
	for item in purchase.items.all():
		if item.part:
			if purchase.is_return:
				# original was a return (stock was decreased) -> restore quantities
				item.part.quantity = item.part.quantity + item.quantity
			else:
				# original was a normal purchase (stock was increased) -> remove quantities
				item.part.quantity = max(0, item.part.quantity - item.quantity)
			item.part.save()
	purchase.delete()
	return redirect('inventory:purchases_list')
