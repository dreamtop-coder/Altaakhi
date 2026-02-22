from django import forms
from cars.maintenance_models import MaintenanceRecord
from services.models import Service

class EditMaintenanceRecordForm(forms.ModelForm):
    service = forms.ModelChoiceField(queryset=Service.objects.all(), label="نوع الخدمة")
    price = forms.DecimalField(max_digits=10, decimal_places=2, label="السعر")
    delivery_date = forms.DateTimeField(label="تاريخ تسليم المركبة", required=False, widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))

    class Meta:
        model = MaintenanceRecord
        # `created_at` is auto-populated (auto_now_add=True) and must not be editable via the form.
        fields = ['service', 'price', 'delivery_date']
