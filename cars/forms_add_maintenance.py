from django import forms
from .models import Car
from services.models import Service

class AddMaintenanceForm(forms.Form):
    plate_number = forms.CharField(label="رقم السيارة", max_length=20, required=False)
    selected_client_car = forms.ModelChoiceField(queryset=Car.objects.none(), required=False, label="اختيار مركبة العميل")
    service = forms.ModelChoiceField(queryset=Service.objects.all(), label="نوع الخدمة", required=False)
    price = forms.DecimalField(max_digits=10, decimal_places=2, label="السعر", required=False)
    notes = forms.CharField(widget=forms.Textarea, required=False, label="ملاحظات")
    maintenance_date = forms.DateField(
        label="تاريخ الصيانة",
        widget=forms.DateInput(attrs={'type': 'date', 'placeholder': 'dd/mm/yyyy'}),
        input_formats=['%Y-%m-%d', '%d/%m/%Y']
    )
    ready_at = forms.DateField(
        label="تاريخ انتهاء التصليح",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'placeholder': 'dd/mm/yyyy'}),
        input_formats=['%Y-%m-%d', '%d/%m/%Y']
    )

    def clean_plate_number(self):
        plate_number = self.cleaned_data['plate_number']
        # plate_number is optional now; only validate if provided
        if not plate_number:
            return plate_number
        from .models import Car
        try:
            car = Car.objects.get(plate_number=plate_number)
        except Car.DoesNotExist:
            raise forms.ValidationError("رقم السيارة غير موجود في قاعدة البيانات.")
        return plate_number

    def get_car_instance(self):
        from .models import Car
        # Prefer explicit selected client car if provided
        sel = self.cleaned_data.get('selected_client_car')
        if sel:
            return sel
        plate = self.cleaned_data.get('plate_number')
        if not plate:
            return None
        try:
            return Car.objects.get(plate_number=plate)
        except Car.DoesNotExist:
            return None
