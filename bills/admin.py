from django.contrib import admin
from .models import Bill, BillLine


class BillLineInline(admin.TabularInline):
    model = BillLine
    extra = 0
    readonly_fields = ()
    fields = ('part', 'description', 'quantity', 'rate', 'amount', 'account_type')


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('bill_number', 'supplier', 'bill_date', 'grand_total', 'status', 'created_at')
    list_filter = ('status', 'bill_date')
    search_fields = ('bill_number', 'supplier__name')
    inlines = [BillLineInline]


@admin.register(BillLine)
class BillLineAdmin(admin.ModelAdmin):
    list_display = ('bill', 'description', 'part', 'quantity', 'rate', 'amount', 'account_type')
    list_filter = ('account_type', 'part')
    search_fields = ('description',)
