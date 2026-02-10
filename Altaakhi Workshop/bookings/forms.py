from django import forms
from .models import Booking


class BookingForm(forms.ModelForm):
    plate_number = forms.CharField(
        label="رقم السيارة",
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "أدخل رقم السيارة"}
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from services.models import Service

        self.fields["service_type"] = forms.ChoiceField(
            choices=[(s.name, s.name) for s in Service.objects.all()],
            label="نوع الخدمة",
            widget=forms.Select(),
        )

    def clean(self):
        cleaned_data = super().clean()
        plate_number = cleaned_data.get("plate_number")
        from cars.models import Car

        try:
            car = Car.objects.get(plate_number=plate_number)
            # لا تمنع الحجز على سيارة مباعة، سيتم تغيير الحالة تلقائياً في save
            cleaned_data["car"] = car
            cleaned_data["client"] = car.client
        except Car.DoesNotExist:
            raise forms.ValidationError(
                "لا يوجد سيارة بهذا الرقم، يرجى تسجيل السيارة أولاً."
            )
        if not cleaned_data.get("client"):
            raise forms.ValidationError("السيارة غير مرتبطة بأي عميل، يرجى ربطها أولاً.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # ربط الحجز بكائن السيارة الصحيح إذا لم يكن مرتبطاً
        if not instance.car and "car" in self.cleaned_data:
            instance.car = self.cleaned_data["car"]
        if not instance.client and "client" in self.cleaned_data:
            instance.client = self.cleaned_data["client"]
        if not instance.status:
            instance.status = "pending"
        if commit:
            instance.save()
        return instance

    class Meta:
        model = Booking
        fields = ["plate_number", "service_type", "service_date", "notes"]
        widgets = {
            "service_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }
