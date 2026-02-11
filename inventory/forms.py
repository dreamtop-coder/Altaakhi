from django import forms
from .models import Supplier, Purchase
from .models import Part


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "phone", "email", "address"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
        }


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ["invoice_number", "date", "amount", "is_return", "notes"]
        widgets = {
            "invoice_number": forms.TextInput(attrs={"class": "form-control"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "amount": forms.NumberInput(attrs={"class": "form-control"}),
            "is_return": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class PartForm(forms.ModelForm):
    class Meta:
        model = Part
        fields = ["name", "quantity", "department", "suppliers", "purchase_price", "sale_price", "low_stock_alert"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "department": forms.Select(attrs={"class": "form-control"}),
            "suppliers": forms.SelectMultiple(attrs={"class": "form-control"}),
            "purchase_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "sale_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "low_stock_alert": forms.NumberInput(attrs={"class": "form-control"}),
        }
