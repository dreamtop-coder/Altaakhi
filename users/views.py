from django.contrib.auth import logout, authenticate, login, get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Group
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from .forms_login import CustomLoginForm
from .forms import CustomUserCreationForm
from .forms_admin import AdminUserCreationForm, AdminUserChangeForm
import secrets
from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .audit import log_audit
from .models import AuditLog
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.decorators import login_required


class AdminForcedPasswordChangeView(PasswordChangeView):
	template_name = 'registration/password_change_form.html'
	success_url = reverse_lazy('password_change_done')

	def form_valid(self, form):
		# clear the force flag after a successful password change
		user = self.request.user
		try:
			if getattr(user, 'force_password_change', False):
				user.force_password_change = False
				user.save(update_fields=['force_password_change'])
		except Exception:
			pass
		return super().form_valid(form)


@login_required
def force_password_change(request):
	"""Allow a logged-in user to set a new password without providing the old one.
	Used when an admin reset the password and we require the user to change it on next login.
	"""
	user = request.user
	if request.method == 'POST':
		form = SetPasswordForm(user, request.POST)
		if form.is_valid():
			form.save()
			try:
				if getattr(user, 'force_password_change', False):
					user.force_password_change = False
					user.save(update_fields=['force_password_change'])
			except Exception:
				pass
			return redirect('password_change_done')
	else:
		form = SetPasswordForm(user)
	return render(request, 'registration/password_change_form.html', {'form': form})


# تسجيل الخروج
def logout_user(request):
	logout(request)
	return redirect('/')


# تسجيل الدخول
def login_user(request):
	if request.method == "POST":
		# Prevent login if user is temporarily locked
		username_attempt = request.POST.get('username') or request.POST.get('email')
		if username_attempt:
			try:
				User = get_user_model()
				u = User.objects.filter(username=username_attempt).first()
				if u and u.locked_until and u.locked_until > timezone.now():
					messages.error(request, 'This account is temporarily locked due to multiple failed login attempts.')
					return render(request, "login.html", {"form": CustomLoginForm()})
			except Exception:
				pass
		form = CustomLoginForm(request, data=request.POST)
		if form.is_valid():
			user = form.get_user()
			# reset failed attempts on successful login
			try:
				user.failed_login_attempts = 0
				user.locked_until = None
				user.save(update_fields=['failed_login_attempts', 'locked_until'])
			except Exception:
				pass
			login(request, user)
			# If admin reset flagged this account, force password change
			try:
				if getattr(user, 'force_password_change', False):
					return redirect('force_password_change')
			except Exception:
				pass
			return redirect("dashboard")
	else:
		form = CustomLoginForm()
	return render(request, "login.html", {"form": form})


def register_user(request):
	if request.method == "POST":
		form = CustomUserCreationForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, "User created successfully.")
			return redirect("users_list")
	else:
		form = CustomUserCreationForm()
	return render(request, "register_user.html", {"form": form})


# --- Admin: User Management MVP ---
def staff_required(view_func):
	return user_passes_test(lambda u: u.is_staff)(view_func)


@staff_required
def list_users(request):
	User = get_user_model()
	q = request.GET.get('q', '').strip()
	users = User.objects.all().order_by('-date_joined')

	# Filter by group
	selected_group = request.GET.get('group', '').strip()
	if selected_group:
		try:
			# allow group id or name
			if selected_group.isdigit():
				users = users.filter(groups__id=int(selected_group))
			else:
				users = users.filter(groups__name__icontains=selected_group)
		except Exception:
			pass

	# Filter by status
	status = request.GET.get('status', '').strip().lower()
	if status == 'active':
		users = users.filter(is_active=True)
	elif status == 'inactive':
		users = users.filter(is_active=False)

	# Filter by locked status
	locked = request.GET.get('locked', '').strip().lower()
	if locked == 'locked':
		users = users.filter(locked_until__gt=timezone.now())
	elif locked == 'unlocked':
		users = users.filter(Q(locked_until__isnull=True) | Q(locked_until__lte=timezone.now()))

	# Free-text search across username, email, first_name, last_name
	if q:
		users = users.filter(
			Q(username__icontains=q) | Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
		)

	# Pagination
	per_page = request.GET.get('per_page')
	try:
		per_page = int(per_page)
		if per_page not in (10, 25):
			per_page = 25
	except Exception:
		per_page = 25

	paginator = Paginator(users, per_page)
	page = request.GET.get('page')
	try:
		users_page = paginator.page(page)
	except PageNotAnInteger:
		users_page = paginator.page(1)
	except EmptyPage:
		users_page = paginator.page(paginator.num_pages)

	# base querystring without page param for pagination links
	qs = request.GET.copy()
	if 'page' in qs:
		qs.pop('page')
	base_qs = qs.urlencode()

	groups = Group.objects.all().order_by('name')

	return render(request, 'users/list.html', {
		'users': users_page,
		'q': q,
		'groups': groups,
		'selected_group': selected_group,
		'status': status,
		'locked': locked,
		'per_page': per_page,
		'base_qs': base_qs,
		'now': timezone.now(),
	})


@staff_required
def create_user(request):
	if request.method == 'POST':
		form = AdminUserCreationForm(request.POST)
		if form.is_valid():
			user = form.save()
			# assign groups if provided
			groups = form.cleaned_data.get('groups')
			if groups is not None:
				user.groups.set(groups)
			# Audit log: user created
			try:
				log_audit(user=request.user, action=AuditLog.ACTION_CREATE_USER, target_user=user, request=request)
			except Exception:
				pass
			messages.success(request, 'User created.')
			return redirect('users_list')
	else:
		form = AdminUserCreationForm()
	return render(request, 'users/form.html', {'form': form, 'creating': True})


@staff_required
def edit_user(request, pk):
	User = get_user_model()
	user = get_object_or_404(User, pk=pk)
	if request.method == 'POST':
		form = AdminUserChangeForm(request.POST, instance=user)
		if form.is_valid():
			user = form.save()
			# update groups
			groups = form.cleaned_data.get('groups')
			if groups is not None:
				user.groups.set(groups)
				# Audit log: user edited
				try:
					log_audit(user=request.user, action=AuditLog.ACTION_EDIT_USER, target_user=user, request=request)
				except Exception:
					pass
			messages.success(request, 'User updated.')
			return redirect('users_list')
	else:
		form = AdminUserChangeForm(instance=user)
	return render(request, 'users/form.html', {'form': form, 'creating': False, 'user_obj': user})


@staff_required
def toggle_user_active(request, pk):
	User = get_user_model()
	user = get_object_or_404(User, pk=pk)
	user.is_active = not user.is_active
	user.save()
	# Audit log: toggle active
	try:
		log_audit(user=request.user, action=AuditLog.ACTION_TOGGLE_ACTIVE, target_user=user, request=request, extra={'is_active': user.is_active})
	except Exception:
		pass
	messages.success(request, 'User {}.'.format('activated' if user.is_active else 'deactivated'))
	return redirect('users_list')


@login_required
def users_json(request):
	"""Return a simple JSON list of users for client-side dropdowns."""
	try:
		User = get_user_model()
		qs = User.objects.all().values('id', 'first_name', 'last_name', 'username')
		out = []
		for u in qs:
			name = (u.get('first_name') or '').strip() or (u.get('username') or '')
			if u.get('last_name'):
				ln = (u.get('last_name') or '').strip()
				if ln:
					name = (name + ' ' + ln).strip()
			out.append({'id': u['id'], 'name': name})
		return JsonResponse({'success': True, 'users': out})
	except Exception as exc:
		return JsonResponse({'success': False, 'error': str(exc)}, status=500)


@staff_required
def audit_logs(request):
	"""List audit logs with simple filtering and pagination."""
	logs_qs = AuditLog.objects.select_related('user', 'target_user').all()
	q = request.GET.get('q', '').strip()
	if q:
		logs_qs = logs_qs.filter(
			Q(user__username__icontains=q) | Q(target_user__username__icontains=q) | Q(action__icontains=q)
		)

	# Pagination
	per_page = request.GET.get('per_page')
	try:
		per_page = int(per_page)
		if per_page not in (10, 25):
			per_page = 25
	except Exception:
		per_page = 25

	paginator = Paginator(logs_qs, per_page)
	page = request.GET.get('page')
	try:
		logs_page = paginator.page(page)
	except PageNotAnInteger:
		logs_page = paginator.page(1)
	except EmptyPage:
		logs_page = paginator.page(paginator.num_pages)

	qs = request.GET.copy()
	if 'page' in qs:
		qs.pop('page')
	base_qs = qs.urlencode()

	return render(request, 'users/audit_logs.html', {
		'logs': logs_page,
		'q': q,
		'per_page': per_page,
		'base_qs': base_qs,
	})


@staff_required
@require_POST
def unlock_user(request, pk):
	User = get_user_model()
	user = get_object_or_404(User, pk=pk)
	# capture previous state for audit/email
	prev_failed = user.failed_login_attempts or 0
	prev_locked = user.locked_until

	user.failed_login_attempts = 0
	user.locked_until = None
	user.save(update_fields=['failed_login_attempts', 'locked_until'])
	try:
		log_audit(user=request.user, action=AuditLog.ACTION_UNLOCK, target_user=user, request=request)
	except Exception:
		pass
	# send admin notification email if configured
	try:
		admin_emails = []
		if getattr(settings, 'ADMIN_NOTIFICATION_EMAILS', None):
			a = settings.ADMIN_NOTIFICATION_EMAILS
			admin_emails = list(a) if isinstance(a, (list, tuple)) else [a]
		elif getattr(settings, 'ADMINS', None):
			admin_emails = [email for name, email in settings.ADMINS if email]

		if admin_emails:
			subject = render_to_string('registration/admin_user_unlocked_subject.txt', {'actor': request.user, 'target_user': user}).strip()
			context = {
				'actor': request.user,
				'target_user': user,
				'prev_failed': prev_failed,
				'prev_locked': prev_locked,
				'time': timezone.now(),
			}
			html_body = render_to_string('registration/admin_user_unlocked_email.html', context)
			text_body = strip_tags(html_body)
			msg = EmailMultiAlternatives(subject, text_body, getattr(settings, 'DEFAULT_FROM_EMAIL', None), admin_emails)
			msg.attach_alternative(html_body, 'text/html')
			msg.send(fail_silently=True)
	except Exception:
		pass
	# send notification to the user whose account was unlocked
	try:
		if user.email:
			subject_u = render_to_string('registration/user_unlocked_subject.txt', {'actor': request.user, 'target_user': user}).strip()
			context_u = {
				'actor': request.user,
				'target_user': user,
				'prev_failed': prev_failed,
				'prev_locked': prev_locked,
				'time': timezone.now(),
			}
			html_body_u = render_to_string('registration/user_unlocked_email.html', context_u)
			text_body_u = strip_tags(html_body_u)
			msg_u = EmailMultiAlternatives(subject_u, text_body_u, getattr(settings, 'DEFAULT_FROM_EMAIL', None), [user.email])
			msg_u.attach_alternative(html_body_u, 'text/html')
			msg_u.send(fail_silently=True)
	except Exception:
		pass

	# If AJAX request, return JSON so client can update without reload
	if request.headers.get('x-requested-with') == 'XMLHttpRequest':
		return JsonResponse({'status': 'ok', 'message': 'User unlocked.'})

	messages.success(request, 'User unlocked.')
	return redirect('users_list')


@staff_required
@require_POST
def reset_user_password(request, pk):
	User = get_user_model()
	try:
		user = User.objects.get(id=pk)
	except User.DoesNotExist:
		messages.error(request, 'User not found.')
		return redirect('users_list')



	# If user has no email, fallback to setting a temporary password
	if not user.email:
		new_pass = User.objects.make_random_password()
		user.set_password(new_pass)
		user.force_password_change = True
		user.save()
		print('Temporary password:', new_pass)
		# Audit log: reset password (fallback)
		try:
			log_audit(user=request.user, action=AuditLog.ACTION_RESET_PASSWORD, target_user=user, request=request, extra={'email': False, 'email_sent': False})
		except Exception:
			pass
		messages.success(request, f'Temporary password set: {new_pass}')
		return redirect('users_list')

	form = PasswordResetForm({'email': user.email})

	if form.is_valid():
		try:
			form.save(
				request=request,
				use_https=False,
				from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
				html_email_template_name='registration/password_reset_email.html'
			)
			print('Email sent to:', user.email)
			# mark forced change and audit log: reset password email sent
			try:
				user.force_password_change = True
				user.save(update_fields=['force_password_change'])
			except Exception:
				pass
			try:
				log_audit(user=request.user, action=AuditLog.ACTION_RESET_PASSWORD, target_user=user, request=request, extra={'email': True, 'email_sent': True})
			except Exception:
				pass
			messages.success(request, f'Password reset email sent to {user.email}.')
		except Exception:
			# fallback to temporary password on send failure
			new_pass = User.objects.make_random_password()
			user.set_password(new_pass)
			user.save()
			print('Temporary password (send failed):', new_pass)
			# Audit log: reset password with send failure
			try:
				log_audit(user=request.user, action=AuditLog.ACTION_RESET_PASSWORD, target_user=user, request=request, extra={'email': True, 'email_sent': False})
			except Exception:
				pass
			messages.warning(request, f'Email send failed; temporary password set: {new_pass}')
	else:
		print('Form not valid')
		messages.error(request, 'Password reset form invalid.')

	return redirect('users_list')
