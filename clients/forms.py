from django import forms
from .models import Client

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['first_name', 'customer_id', 'phone_number', 'address', 'email', 'created_at']
        labels = {
            'first_name': 'Name',
            'customer_id': 'Customer ID',
            'phone_number': 'Phone',
            'address': 'Address',
            'email': 'Email',
            'created_at': 'Added On',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address'}),
            'customer_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer ID (unique)'}),
            'created_at': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
