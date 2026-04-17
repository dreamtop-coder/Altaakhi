from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from .brand_models import CarBrand, CarModel


admin.site.register(CarBrand)
admin.site.register(CarModel)

# تسجيل موديل السيارة في لوحة الإدارة
from .models import Car
@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
	list_display = ('plate_number', 'client', 'brand', 'model', 'status_display')
	# use custom filters to show English labels in the admin sidebar
	list_filter = ('brand_filter', 'status_filter')
	search_fields = ('plate_number', 'client__name', 'vin_number')
	fields = ('client', 'plate_number', 'brand', 'model', 'year', 'color', 'fuel_type', 'vin_number', 'status', 'notes')

	def status_display(self, obj):
		mapping = {
			'waiting': 'Waiting',
			'in_progress': 'In Progress',
			'pending_payment': 'Pending Payment',
			'paid_waiting_collection': 'Paid - Waiting Collection',
			'done': 'Done',
			'active': 'Active',
			'ready': 'Ready',
			'sold': 'Sold',
		}
		return mapping.get(obj.status, obj.status)
	status_display.short_description = 'Status'
	status_display.admin_order_field = 'status'

	def formfield_for_choice_field(self, db_field, request, **kwargs):
		# Override choice labels in the admin form to English only for UI clarity.
		if db_field.name == 'fuel_type':
			kwargs['choices'] = [
				('gasoline', 'Gasoline'),
				('diesel', 'Diesel'),
				('electric', 'Electric'),
				('hybrid', 'Hybrid'),
			]
		if db_field.name == 'status':
			kwargs['choices'] = [
				('waiting', 'Waiting'),
				('in_progress', 'In Progress'),
				('pending_payment', 'Pending Payment'),
				('paid_waiting_collection', 'Paid - Waiting Collection'),
				('done', 'Done'),
				('active', 'Active'),
				('ready', 'Ready'),
				('sold', 'Sold'),
			]
		return super().formfield_for_choice_field(db_field, request, **kwargs)


class CarStatusFilter(SimpleListFilter):
	title = 'Status'
	parameter_name = 'status'

	def lookups(self, request, model_admin):
		return (
			('waiting', 'Waiting'),
			('in_progress', 'In Progress'),
			('pending_payment', 'Pending Payment'),
			('paid_waiting_collection', 'Paid - Waiting Collection'),
			('done', 'Done'),
			('active', 'Active'),
			('ready', 'Ready'),
			('sold', 'Sold'),
		)

	def queryset(self, request, queryset):
		if self.value():
			return queryset.filter(status=self.value())
		return queryset


class CarBrandFilter(SimpleListFilter):
	title = 'Brand'
	parameter_name = 'brand'

	def lookups(self, request, model_admin):
		return tuple((str(b.id), b.name) for b in CarBrand.objects.all())

	def queryset(self, request, queryset):
		if self.value():
			return queryset.filter(brand_id=self.value())
		return queryset

# Wire the filters into the admin registry for this model
admin.site._registry[Car].list_filter = (CarStatusFilter, CarBrandFilter)
