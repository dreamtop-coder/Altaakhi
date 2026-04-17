from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.contrib.auth import get_user_model
from django.utils import timezone
import datetime
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
from .models import AuditLog


def _get_client_ip(request):
	if not request:
		return None
	x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
	if x_forwarded:
		# X-Forwarded-For may contain multiple IPs
		return x_forwarded.split(',')[0].strip()
	return request.META.get('REMOTE_ADDR')


def log_audit(user=None, action=None, target_user=None, request=None, extra=None):
	"""Create an AuditLog entry.
	user: actor (may be None for system)
	action: one of AuditLog.ACTION_* constants
	target_user: optional affected user
	request: optional HttpRequest to extract IP
	extra: optional dict for additional metadata
	"""
	ip = _get_client_ip(request)
	if extra is None:
		extra = {}

	entry = AuditLog.objects.create(
		user=user,
		action=action,
		target_user=target_user,
		ip_address=ip,
		extra=extra,
	)
	return entry


@receiver(user_logged_in)
def _log_user_logged_in(sender, request, user, **kwargs):
	# Log login events: actor is the user themselves
	try:
		log_audit(user=user, action=AuditLog.ACTION_LOGIN, target_user=user, request=request, extra={'session_key': request.session.session_key if hasattr(request, 'session') else None})
	except Exception:
		# Do not raise if logging fails
		pass


@receiver(user_login_failed)
def _log_user_login_failed(sender, credentials, request, **kwargs):
	"""Log failed login attempts and optionally lock account after threshold."""
	username = credentials.get('username') if credentials else None
	ip = _get_client_ip(request)
	target_user = None
	try:
		User = get_user_model()
		if username:
			target_user = User.objects.filter(username=username).first()
			if target_user:
				# increment counter and possibly lock
				threshold = getattr(settings, 'AUTH_LOCKOUT_THRESHOLD', 5)
				duration_min = getattr(settings, 'AUTH_LOCKOUT_DURATION_MINUTES', 15)
				old_failed = target_user.failed_login_attempts or 0
				new_failed = old_failed + 1
				target_user.failed_login_attempts = new_failed
				locked_now = False
				if new_failed >= threshold:
					# lock user
					target_user.locked_until = timezone.now() + datetime.timedelta(minutes=duration_min)
					# only treat as newly locked if previously below threshold
					if old_failed < threshold:
						locked_now = True
				target_user.save(update_fields=['failed_login_attempts', 'locked_until'])
				# send notification email if newly locked
				if locked_now and target_user.email:
					try:
						subject = render_to_string('registration/account_locked_subject.txt', {'user': target_user}).strip()
						context = {
							'user': target_user,
							'locked_until': target_user.locked_until,
						}
						# build a password reset URL if request available
						if request is not None:
							scheme = 'https' if request.is_secure() else 'http'
							host = request.get_host()
							try:
								pw_url = reverse('password_reset')
								context['password_reset_url'] = f"{scheme}://{host}{pw_url}"
							except Exception:
								context['password_reset_url'] = None
						html_body = render_to_string('registration/account_locked_email.html', context)
						text_body = strip_tags(html_body)
						msg = EmailMultiAlternatives(subject, text_body, getattr(settings, 'DEFAULT_FROM_EMAIL', None), [target_user.email])
						msg.attach_alternative(html_body, 'text/html')
						msg.send(fail_silently=True)
					except Exception:
						# ignore email failures
						pass
	except Exception:
		target_user = None

	try:
		extra = {'username': username, 'ip': ip}
		if target_user:
			extra.update({'failed_count': target_user.failed_login_attempts, 'locked_until': target_user.locked_until.isoformat() if target_user.locked_until else None})
		log_audit(user=None, action=AuditLog.ACTION_FAILED_LOGIN, target_user=target_user, request=request, extra=extra)
	except Exception:
		pass
