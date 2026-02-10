from django.shortcuts import render, redirect, get_object_or_404
from .brand_models import CarBrand, CarModel
from .brand_forms import CarBrandForm, CarModelForm

# --- إدارة شركات الصنع ---
from django.contrib.auth.decorators import login_required


@login_required
def brands_list(request):
    from .brand_models import CarBrand, CarModel

    message = None
    if request.method == "POST":
        brand_name = request.POST.get("brand_name", "").strip()
        model_name = request.POST.get("model_name", "").strip()
        if brand_name and model_name:
            brand, created = CarBrand.objects.get_or_create(name=brand_name)
            if not CarModel.objects.filter(brand=brand, name=model_name).exists():
                CarModel.objects.create(brand=brand, name=model_name)
                message = "تم الحفظ بنجاح."
            else:
                message = "الموديل موجود بالفعل لهذه الشركة."
        else:
            message = "يرجى إدخال اسم الشركة واسم الموديل."
    brands = CarBrand.objects.all()
    models = CarModel.objects.select_related("brand").order_by("brand__name", "name")
    return render(
        request,
        "brands_list.html",
        {"brands": brands, "models": models, "message": message},
    )


@login_required
def add_brand(request):
    if request.method == "POST":
        form = CarBrandForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("brands_list")
    else:
        form = CarBrandForm()
    return render(request, "add_brand.html", {"form": form})


@login_required
def edit_brand(request, brand_id):
    brand = get_object_or_404(CarBrand, id=brand_id)
    if request.method == "POST":
        form = CarBrandForm(request.POST, instance=brand)
        if form.is_valid():
            form.save()
            return redirect("brands_list")
    else:
        form = CarBrandForm(instance=brand)
    return render(request, "edit_brand.html", {"form": form, "brand": brand})


@login_required
def delete_brand(request, brand_id):
    brand = get_object_or_404(CarBrand, id=brand_id)
    brand.delete()
    return redirect("brands_list")


# --- إدارة موديلات السيارات ---
@login_required
def models_list(request):
    models = CarModel.objects.select_related("brand").all()
    return render(request, "models_list.html", {"models": models})


@login_required
def add_model(request):
    if request.method == "POST":
        form = CarModelForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("models_list")
    else:
        form = CarModelForm()
    return render(request, "add_model.html", {"form": form})


@login_required
def edit_model(request, model_id):
    model = get_object_or_404(CarModel, id=model_id)
    if request.method == "POST":
        form = CarModelForm(request.POST, instance=model)
        if form.is_valid():
            form.save()
            return redirect("models_list")
    else:
        form = CarModelForm(instance=model)
    return render(request, "edit_model.html", {"form": form, "model": model})


@login_required
def delete_model(request, model_id):
    model = get_object_or_404(CarModel, id=model_id)
    model.delete()
    return redirect("models_list")
