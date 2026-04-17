
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
import datetime

class User(AbstractUser):
	phone_number = models.CharField(max_length=20, blank=True, null=True)
	role = models.CharField(
		max_length=50,
		blank=True,
		null=True,
		help_text="دور المستخدم في النظام مثل: مدير، موظف، محاسب، فني، استقبال"
	)
	is_active = models.BooleanField(default=True)

	# Security: failed login tracking and temporary lock
	failed_login_attempts = models.IntegerField(default=0)
	locked_until = models.DateTimeField(null=True, blank=True)

	# Require password change on next login (set when admin resets password)
	force_password_change = models.BooleanField(default=False)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.username


class AuditLog(models.Model):
	ACTION_RESET_PASSWORD = 'RESET_PASSWORD'
	ACTION_TOGGLE_ACTIVE = 'TOGGLE_ACTIVE'
	ACTION_EDIT_USER = 'EDIT_USER'
	ACTION_CREATE_USER = 'CREATE_USER'
	ACTION_LOGIN = 'LOGIN'
	ACTION_FAILED_LOGIN = 'FAILED_LOGIN'
	ACTION_UNLOCK = 'UNLOCK_USER'
	
	ACTION_CHOICES = [
		(ACTION_RESET_PASSWORD, 'Reset Password'),
		(ACTION_TOGGLE_ACTIVE, 'Toggle Active'),
		(ACTION_EDIT_USER, 'Edit User'),
		(ACTION_CREATE_USER, 'Create User'),
		(ACTION_LOGIN, 'Login'),
		(ACTION_FAILED_LOGIN, 'Failed Login'),
		(ACTION_UNLOCK, 'Unlock User'),
	]

	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='audit_logs_by'
	)
	action = models.CharField(max_length=50, choices=ACTION_CHOICES)
	target_user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='audit_logs_for'
	)
	ip_address = models.GenericIPAddressField(null=True, blank=True)
	extra = models.JSONField(null=True, blank=True)
	timestamp = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-timestamp']

	def __str__(self):
		actor = self.user.username if self.user else 'system'
		target = self.target_user.username if self.target_user else ''
		return f"{self.timestamp.isoformat()} {actor} {self.action} {target}"
