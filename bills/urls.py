from django.urls import path
from .views import (
    add_bill, bills_list, bill_detail, delete_bills, last_purchase_price, edit_bill,
    supplier_bills_json, vendor_payments_list, add_vendor_payment, delete_vendor_payments
)
from .views import vendor_payment_detail
from .views import migrate_session_bills_view

urlpatterns = [
    path('', bills_list, name='bills_list'),
    path('add/', add_bill, name='add_bill'),
    path('view/<int:bill_id>/', bill_detail, name='bill_detail'),
    path('edit/<int:bill_id>/', edit_bill, name='edit_bill'),
    path('view/session/<int:session_index>/', bill_detail, name='bill_detail_session'),
    path('delete/', delete_bills, name='bills_delete'),
    path('last_price/', last_purchase_price, name='bills_last_price'),
    path('supplier-bills/', supplier_bills_json, name='supplier_bills_json'),
    path('payments/', vendor_payments_list, name='vendor_payments_list'),
    path('payments/add/', add_vendor_payment, name='add_vendor_payment'),
    path('payments/view/<int:payment_id>/', vendor_payment_detail, name='vendor_payment_detail'),
    path('payments/delete/', delete_vendor_payments, name='delete_vendor_payments'),
    path('migrate-session/', migrate_session_bills_view, name='migrate_session_bills'),
]
