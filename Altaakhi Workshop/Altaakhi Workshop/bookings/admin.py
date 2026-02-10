from django.contrib import admin
from .models import Booking



@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("phone", "service_type", "service_date", "created_at")
    search_fields = ("phone", "service_type")
    list_filter = ("service_type", "service_date")
