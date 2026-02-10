from django import forms
from .models import Service


class MaintenanceRecordForm(forms.Form):
    service = forms.ModelChoiceField(queryset=Service.objects.all(), label="نوع الخدمة")
    price = forms.DecimalField(max_digits=10, decimal_places=2, label="السعر")
    notes = forms.CharField(widget=forms.Textarea, required=False, label="ملاحظات")
