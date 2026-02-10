from .models import User
from django.contrib.auth.forms import UserCreationForm


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email", "phone_number", "role", "password1", "password2")
        labels = {
            "username": "اسم المستخدم",
            "email": "البريد الإلكتروني",
            "phone_number": "رقم الجوال",
            "role": "الدور",
            "password1": "كلمة المرور",
            "password2": "تأكيد كلمة المرور",
        }
