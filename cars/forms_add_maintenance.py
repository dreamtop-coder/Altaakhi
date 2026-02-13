from django import forms
from datetime import date
from services.models import Service


class AddMaintenanceForm(forms.Form):
    plate_number = forms.CharField(label="رقم السيارة", max_length=20)
    service = forms.ModelChoiceField(
        queryset=Service.objects.all(),
        label="نوع الخدمة",
        required=False,
        widget=forms.Select(),
    )
    price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="السعر",
        required=False,
        widget=forms.NumberInput(),
    )
    notes = forms.CharField(widget=forms.Textarea, required=False, label="ملاحظات")
    maintenance_date = forms.DateField(
        label="تاريخ الصيانة",
        widget=forms.DateInput(attrs={"type": "date"}),
        initial=date.today,
    )
    ready_at = forms.DateField(
        label="تاريخ انتهاء التصليح",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def clean_plate_number(self):
        plate_number = self.cleaned_data["plate_number"]
        from .models import Car

        try:
            Car.objects.get(plate_number=plate_number)
        except Car.DoesNotExist:
            raise forms.ValidationError("رقم السيارة غير موجود في قاعدة البيانات.")
        return plate_number

    def get_car_instance(self):
        from .models import Car

        return Car.objects.get(plate_number=self.cleaned_data["plate_number"])

    def clean_maintenance_date(self):
        val = self.cleaned_data.get('maintenance_date')
        if not val:
            raise forms.ValidationError('الرجاء إدخال تاريخ صالح.')
        # ensure it's a date and within a reasonable range
        try:
            if not hasattr(val, 'year'):
                raise ValueError()
            if val.year < 1900 or val.year > 2100:
                raise forms.ValidationError('الرجاء إدخال تاريخ صالح بين 1900 و2100.')
        except Exception:
            raise forms.ValidationError('الرجاء إدخال تاريخ صالح.')
        return val
