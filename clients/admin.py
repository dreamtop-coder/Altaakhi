from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
	list_display = ('customer_id', 'first_name', 'last_name', 'status_display')
	# Use custom filters to present English labels in the sidebar filters
	list_filter = ('brand', 'client_filter_status', 'client_filter_comm')
	search_fields = ('first_name', 'last_name', 'phone_number', 'customer_id')

	def formfield_for_choice_field(self, db_field, request, **kwargs):
		# Show English choice labels in admin form (UI-only)
		if db_field.name == 'status':
			kwargs['choices'] = [
				('active', 'Active'),
				('inactive', 'Inactive'),
			]
		if db_field.name == 'communication_preference':
			kwargs['choices'] = [
				('email', 'Email'),
				('phone', 'Phone'),
				('sms', 'SMS'),
			]
		return super().formfield_for_choice_field(db_field, request, **kwargs)

	def status_display(self, obj):
		mapping = {
			'active': 'Active',
			'inactive': 'Inactive',
		}
		return mapping.get(obj.status, obj.status)
	status_display.short_description = 'Status'
	status_display.admin_order_field = 'status'


class ClientStatusFilter(SimpleListFilter):
	title = 'Status'
	parameter_name = 'status'

	def lookups(self, request, model_admin):
		return (
			('active', 'Active'),
			('inactive', 'Inactive'),
		)

	def queryset(self, request, queryset):
		if self.value():
			return queryset.filter(status=self.value())
		return queryset


class ClientCommFilter(SimpleListFilter):
	title = 'Communication preference'
	parameter_name = 'communication_preference'

	def lookups(self, request, model_admin):
		return (
			('email', 'Email'),
			('phone', 'Phone'),
			('sms', 'SMS'),
		)

	def queryset(self, request, queryset):
		if self.value():
			return queryset.filter(communication_preference=self.value())
		return queryset

# Register the custom filters under internal names expected in list_filter
admin.site._registry[Client].list_filter = (ClientStatusFilter, ClientCommFilter) 

