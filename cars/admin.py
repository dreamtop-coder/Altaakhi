from django.contrib import admin
from .brand_models import CarBrand, CarModel


admin.site.register(CarBrand)
admin.site.register(CarModel)

# تسجيل موديل السيارة في لوحة الإدارة
from .models import Car
@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
	list_display = ('plate_number', 'client', 'brand', 'model', 'status')
	list_filter = ('status', 'brand')
	search_fields = ('plate_number', 'client__name', 'vin_number')
	fields = ('client', 'plate_number', 'brand', 'model', 'year', 'color', 'fuel_type', 'vin_number', 'status', 'notes')
