from django import forms
from .models import Car
from .brand_models import CarBrand, CarModel

class CarForm(forms.ModelForm):
    brand = forms.ModelChoiceField(queryset=CarBrand.objects.all(), label="Brand")
    model = forms.ModelChoiceField(queryset=CarModel.objects.none(), label="Model")

    class Meta:
        model = Car
        fields = ['plate_number', 'brand', 'model', 'year', 'color', 'fuel_type', 'vin_number', 'status', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Override labels and choice labels for UI-only (keep DB values intact)
        self.fields['fuel_type'].label = 'Fuel type'
        self.fields['status'].label = 'Status'
        # Provide English labels for the select choices (same choice keys preserved)
        try:
            self.fields['fuel_type'].choices = [
                ('gasoline', 'Gasoline'),
                ('diesel', 'Diesel'),
                ('electric', 'Electric'),
                ('hybrid', 'Hybrid'),
            ]
        except Exception:
            pass
        try:
            self.fields['status'].choices = [
                ('waiting', 'Waiting'),
                ('in_progress', 'In Progress'),
                ('pending_payment', 'Pending Payment'),
                ('paid_waiting_collection', 'Paid - Waiting Collection'),
                ('done', 'Done'),
                ('active', 'Active'),
                ('ready', 'Ready'),
                ('sold', 'Sold'),
            ]
        except Exception:
            pass
        if 'brand' in self.data:
            try:
                brand_id = int(self.data.get('brand'))
                self.fields['model'].queryset = CarModel.objects.filter(brand_id=brand_id).order_by('name')
            except (ValueError, TypeError):
                self.fields['model'].queryset = CarModel.objects.none()
        elif self.instance.pk and self.instance.brand:
            self.fields['model'].queryset = CarModel.objects.filter(brand=self.instance.brand).order_by('name')
        else:
            self.fields['model'].queryset = CarModel.objects.none()
