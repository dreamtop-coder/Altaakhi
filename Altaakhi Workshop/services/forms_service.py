from django import forms
from services.models import Service


class ServiceFormNoCar(forms.ModelForm):
    class Meta:
        model = Service
        exclude = ["car"]
