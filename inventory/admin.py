from django.contrib import admin
from .models import Supplier, Part, Purchase, PurchaseItem
from .forms import PartForm


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
	list_display = ("name", "phone", "email")


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
	list_display = ("name", "department", "quantity", "is_stock_item", "track_purchases", "track_sales")
	list_filter = ("department", "is_stock_item", "track_purchases", "track_sales")
	search_fields = ("name",)
	filter_horizontal = ("suppliers",)
	form = PartForm


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
	list_display = ("supplier", "date", "amount", "is_return")


@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
	list_display = ("part_name", "quantity", "unit_price", "total_price")

