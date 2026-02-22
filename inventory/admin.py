from django.contrib import admin
from .models import Supplier, Part


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
	list_display = ('name', 'phone', 'email', 'address', 'amount')
	search_fields = ('name', 'phone', 'email', 'address')


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
	list_display = ('name', 'quantity', 'department', 'supplier', 'low_stock_alert')
	search_fields = ('name',)
