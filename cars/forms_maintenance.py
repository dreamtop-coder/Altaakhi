from django import forms
from .models import Service

class MaintenanceRecordForm(forms.Form):
    service = forms.ModelChoiceField(queryset=Service.objects.all(), label="نوع الخدمة", required=False)
    price = forms.DecimalField(max_digits=10, decimal_places=3, label="السعر")
    created_at = forms.DateTimeField(label="تاريخ الصيانة", required=False, widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    delivery_date = forms.DateTimeField(label="تاريخ تسليم المركبة", required=False, widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    notes = forms.CharField(widget=forms.Textarea, required=False, label="ملاحظات")
