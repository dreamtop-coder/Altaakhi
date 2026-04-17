from django.shortcuts import render, redirect, get_object_or_404
from .brand_models import CarBrand, CarModel
from .brand_forms import CarBrandForm, CarModelForm

# --- إدارة شركات الصنع ---
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from urllib.parse import quote as urlquote
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

@login_required
def brands_list(request):
    from .brand_models import CarBrand, CarModel
    message = None
    if request.method == 'POST':
        brand_name = request.POST.get('brand_name', '').strip()
        model_name = request.POST.get('model_name', '').strip()
        if brand_name and model_name:
            brand, created = CarBrand.objects.get_or_create(name=brand_name)
            if not CarModel.objects.filter(brand=brand, name=model_name).exists():
                CarModel.objects.create(brand=brand, name=model_name)
                message = 'Saved successfully.'
            else:
                message = 'Model already exists for this brand.'
        else:
            message = 'Please enter brand name and model name.'
    brands = CarBrand.objects.all()
    models = CarModel.objects.select_related('brand').order_by('brand__name', 'name')
    return render(request, 'brands_list.html', {'brands': brands, 'models': models, 'message': message})

@login_required
def add_brand(request):
    message = None
    # if redirected here with exists param, prefill name and show message
    if request.method == 'GET' and request.GET.get('exists'):
        pre_name = request.GET.get('name', '')
        form = CarBrandForm(initial={'name': pre_name})
        message = 'Brand already exists.'
        return render(request, 'add_brand.html', {'form': form, 'message': message})

    if request.method == 'POST':
        form = CarBrandForm(request.POST)
        if form.is_valid():
            brand = form.save()
            # If AJAX request, return JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'id': brand.id, 'name': brand.name})
            return redirect('brands_list')
        else:
            # If AJAX request, return JSON error message(s)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Collect form errors
                errors = form.errors.get('name') or form.non_field_errors() or ["Invalid input"]
                return JsonResponse({'success': False, 'errors': errors})
            # non-AJAX: redirect to add page with exists hint when duplicate
            name = request.POST.get('name', '').strip()
            if name and CarBrand.objects.filter(name__iexact=name).exists():
                url = reverse('add_brand') + '?exists=1&name=' + urlquote(name)
                return redirect(url)
    else:
        form = CarBrandForm()
    return render(request, 'add_brand.html', {'form': form})

@login_required
def edit_brand(request, brand_id):
    brand = get_object_or_404(CarBrand, id=brand_id)
    if request.method == 'POST':
        form = CarBrandForm(request.POST, instance=brand)
        if form.is_valid():
            form.save()
            return redirect('brands_list')
    else:
        form = CarBrandForm(instance=brand)
    return render(request, 'edit_brand.html', {'form': form, 'brand': brand})

@login_required
def delete_brand(request, brand_id):
    brand = get_object_or_404(CarBrand, id=brand_id)
    brand.delete()
    return redirect('brands_list')

# --- إدارة موديلات السيارات ---
@login_required
def models_list(request):
    models = CarModel.objects.select_related('brand').all()
    return render(request, 'models_list.html', {'models': models})

@login_required
def add_model(request):
    if request.method == 'POST':
        form = CarModelForm(request.POST)
        if form.is_valid():
            model = form.save()
            # support AJAX requests returning JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'id': model.id, 'name': model.name, 'brand_id': model.brand.id})
            return redirect('models_list')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = form.errors.get('name') or form.non_field_errors() or ["Invalid input"]
                return JsonResponse({'success': False, 'errors': errors})
    else:
        form = CarModelForm()
    return render(request, 'add_model.html', {'form': form})

@login_required
def edit_model(request, model_id):
    model = get_object_or_404(CarModel, id=model_id)
    if request.method == 'POST':
        form = CarModelForm(request.POST, instance=model)
        if form.is_valid():
            model = form.save()
            # support AJAX requests returning JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'id': model.id, 'name': model.name, 'brand_id': model.brand.id})
            return redirect('models_list')
        else:
            # for AJAX, return errors as JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = form.errors.get('name') or form.non_field_errors() or ["Invalid input"]
                return JsonResponse({'success': False, 'errors': errors})
    else:
        form = CarModelForm(instance=model)
    return render(request, 'edit_model.html', {'form': form, 'model': model})

@login_required
def delete_model(request, model_id):
    model = get_object_or_404(CarModel, id=model_id)
    model.delete()
    return redirect('models_list')


@require_POST
def models_bulk_delete(request):
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
            m = CarModel.objects.get(pk=int(_id))
            m.delete()
            deleted += 1
        except Exception:
            continue
    return JsonResponse({'ok': True, 'deleted': deleted})


@require_POST
def brands_bulk_delete(request):
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
            b = CarBrand.objects.get(pk=int(_id))
            b.delete()
            deleted += 1
        except Exception:
            continue
    return JsonResponse({'ok': True, 'deleted': deleted})
