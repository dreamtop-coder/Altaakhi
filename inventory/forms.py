from django import forms
from .models import Supplier, Part


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['supplier_code', 'name', 'phone', 'email', 'address', 'amount']
        widgets = {
            'supplier_code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class PartForm(forms.ModelForm):
    class Meta:
        model = Part
        fields = ['name', 'code', 'quantity', 'purchase_price', 'sale_price', 'department', 'supplier', 'track_stock', 'is_purchase', 'is_sale']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sale_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'track_stock': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_purchase': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_sale': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # supplier is optional (parts can come from multiple vendors)
        if 'supplier' in self.fields:
            self.fields['supplier'].required = False

    def clean_code(self):
        code = self.cleaned_data.get('code')

        if not code:
            return code

        # Trim whitespace
        code = code.strip()

        # Allow optional alphabetic prefix followed by digits (e.g. LB0001, MA0001, 0001)
        import re
        m = re.match(r'^([A-Za-z]*)(\d+)$', code)
        if not m:
            from django.core.exceptions import ValidationError
            raise ValidationError('Code must contain digits and may have an alphabetic prefix (e.g. LB0001 or 0001).')

        # Prevent duplicates (case-insensitive)
        qs = Part.objects.filter(code__iexact=code)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            from django.core.exceptions import ValidationError
            raise ValidationError('This code is already in use for another part.')

        return code
