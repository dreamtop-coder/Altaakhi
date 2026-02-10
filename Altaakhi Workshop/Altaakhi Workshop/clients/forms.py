from django import forms
from .models import Client



class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            "first_name",
            "customer_id",
            "phone_number",
            "address",
            "email",
            "created_at",
        ]
        labels = {
            "first_name": "الاسم",
            "customer_id": "الرقم الشخصي",
            "phone_number": "رقم الهاتف",
            "address": "العنوان",
            "email": "البريد الإلكتروني",
            "created_at": "تاريخ الإضافة",
        }
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "الاسم الأول"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "اسم العائلة"}
            ),
            "phone_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "رقم الهاتف"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "البريد الإلكتروني"}
            ),
            "address": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "العنوان"}
            ),
            "customer_id": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "رقم العميل (معرف فريد)"}
            ),
            "created_at": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
        }
