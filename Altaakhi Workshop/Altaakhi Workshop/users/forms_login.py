from django import forms
from django.contrib.auth.forms import AuthenticationForm



class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(label="اسم المستخدم", max_length=150)
    password = forms.CharField(label="كلمة المرور", widget=forms.PasswordInput)
