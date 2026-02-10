from django import forms
from .brand_models import CarBrand, CarModel



class CarBrandForm(forms.ModelForm):
    class Meta:
        model = CarBrand
        fields = ["name"]

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if CarBrand.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError("اسم الشركة موجود بالفعل.")
        return name


class CarModelForm(forms.ModelForm):
    class Meta:
        model = CarModel
        fields = ["brand", "name"]

    def clean(self):
        cleaned_data = super().clean()
        brand = cleaned_data.get("brand")
        name = cleaned_data.get("name", "").strip()
        if brand and name:
            if CarModel.objects.filter(brand=brand, name__iexact=name).exists():
                raise forms.ValidationError("الموديل موجود بالفعل لهذه الشركة.")
        return cleaned_data
