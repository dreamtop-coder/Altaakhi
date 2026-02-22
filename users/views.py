from django.contrib.auth import logout
# تسجيل الخروج
from django.shortcuts import redirect
def logout_user(request):
	logout(request)
	return redirect('/')
from django.contrib.auth import authenticate, login
from .forms_login import CustomLoginForm
# تسجيل الدخول
def login_user(request):
	if request.method == "POST":
		form = CustomLoginForm(request, data=request.POST)
		if form.is_valid():
			user = form.get_user()
			login(request, user)
			return redirect("dashboard")
	else:
		form = CustomLoginForm()
	return render(request, "login.html", {"form": form})

from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from django.contrib import messages

def register_user(request):
	if request.method == "POST":
		form = CustomUserCreationForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, "تم إنشاء المستخدم بنجاح.")
			return redirect("users_list")
	else:
		form = CustomUserCreationForm()
	return render(request, "register_user.html", {"form": form})
