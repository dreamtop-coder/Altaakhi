from django.contrib import admin
from .brand_models import CarBrand, CarModel
from .models import Car



admin.site.register(CarBrand)
admin.site.register(CarModel)

# تسجيل موديل السيارة في لوحة الإدارة

admin.site.register(Car)
