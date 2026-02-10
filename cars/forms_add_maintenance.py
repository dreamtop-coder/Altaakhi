from django import forms
from services.models import Service


class AddMaintenanceForm(forms.Form):
    plate_number = forms.CharField(label="رقم السيارة", max_length=20)
    service = forms.ModelChoiceField(queryset=Service.objects.all(), label="نوع الخدمة")
    price = forms.DecimalField(max_digits=10, decimal_places=2, label="السعر")
    notes = forms.CharField(widget=forms.Textarea, required=False, label="ملاحظات")
    maintenance_date = forms.DateField(
        label="تاريخ الصيانة", widget=forms.DateInput(attrs={"type": "date"})
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
