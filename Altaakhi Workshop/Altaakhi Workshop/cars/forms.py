from django import forms
from .models import Car
from .brand_models import CarBrand, CarModel



class CarForm(forms.ModelForm):
    brand = forms.ModelChoiceField(queryset=CarBrand.objects.all(), label="شركة الصنع")
    model = forms.ModelChoiceField(queryset=CarModel.objects.none(), label="الموديل")

    class Meta:
        model = Car
        fields = [
            "plate_number",
            "brand",
            "model",
            "year",
            "color",
            "fuel_type",
            "vin_number",
            "status",
            "notes",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "brand" in self.data:
            try:
                brand_id = int(self.data.get("brand"))
                self.fields["model"].queryset = CarModel.objects.filter(
                    brand_id=brand_id
                ).order_by("name")
            except (ValueError, TypeError):
                self.fields["model"].queryset = CarModel.objects.none()
        elif self.instance.pk and self.instance.brand:
            self.fields["model"].queryset = CarModel.objects.filter(
                brand=self.instance.brand
            ).order_by("name")
        else:
            self.fields["model"].queryset = CarModel.objects.none()
