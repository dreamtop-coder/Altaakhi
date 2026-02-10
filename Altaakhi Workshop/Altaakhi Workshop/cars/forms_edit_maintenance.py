from django import forms
from cars.maintenance_models import MaintenanceRecord
from services.models import Service



class EditMaintenanceRecordForm(forms.ModelForm):
    service = forms.ModelChoiceField(queryset=Service.objects.all(), label="نوع الخدمة")
    price = forms.DecimalField(max_digits=10, decimal_places=2, label="السعر")
    created_at = forms.DateTimeField(
        label="تاريخ الصيانة",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )
    delivery_date = forms.DateTimeField(
        label="تاريخ تسليم المركبة",
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )

    class Meta:
        model = MaintenanceRecord
        fields = ["service", "price", "created_at", "delivery_date"]
