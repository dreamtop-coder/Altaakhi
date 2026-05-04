from django.contrib import admin

from django.urls import path, include
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from urllib.parse import urlencode
from users.views import AdminForcedPasswordChangeView, force_password_change

from .views import dashboard_summary, revenue_monthly_ajax
from .views_welcome import welcome_page
from clients.views import clients_list, clients_print, bulk_delete_clients
from clients.views import add_client, delete_client, client_detail, edit_client, search_clients_api
from cars.views import cars_ajax_filter, start_maintenance
from cars.views_add import add_car_for_client, get_models_for_brand, edit_car_for_client
from cars.brand_views import brands_list, add_brand, edit_brand, delete_brand, models_list, add_model, edit_model, delete_model, models_bulk_delete, brands_bulk_delete
from cars.dashboard import cars_dashboard
from inventory.views import suppliers_list
from inventory.views import add_supplier, edit_supplier, delete_supplier
from inventory.views import inventory_list, add_part
from inventory.views import edit_part, inventory_bulk_delete
from inventory.views import inventory_search_json, suppliers_search_json
from bills.views import vendor_payments_list, add_vendor_payment, delete_vendor_payments, vendor_payment_detail



urlpatterns = [
    # serve favicon via redirect to static file to avoid 404 during development
    path('favicon.ico', lambda req: redirect('/static/images/favicon.ico')),
    path('', welcome_page, name='home'),
    path('admin/', admin.site.urls),
    path('dashboard/', dashboard_summary, name='dashboard'),
    path('dashboard/revenue_monthly_ajax/', revenue_monthly_ajax, name='revenue_monthly_ajax'),
    # Global search redirect: support legacy `q` -> forward to clients search
    path('global-search/', lambda req: redirect('/clients/?' + urlencode({'search': req.GET.get('q','').strip()})), name='global_search'),
    path('clients/', clients_list, name='clients_list'),
    path('clients/print/', clients_print, name='clients_print'),
    path('clients/bulk-delete/', bulk_delete_clients, name='clients_bulk_delete'),
    path('clients/add/', add_client, name='add_client'),
    path('clients/search/', search_clients_api, name='clients_search_api'),
    path('clients/delete/<int:client_id>/', delete_client, name='delete_client'),
    path('clients/<int:client_id>/', client_detail, name='client_detail'),
    path('clients/<int:client_id>/edit/', edit_client, name='edit_client'),
    path('cars/ajax/filter/', cars_ajax_filter, name='cars_ajax_filter'),
    path('cars/start_maintenance/<int:car_id>/', start_maintenance, name='start_maintenance'),  # أضف هذا السطر
    path('cars/dashboard/', cars_dashboard, name='cars_dashboard'),
    path('clients/<int:client_id>/add_car/', add_car_for_client, name='add_car_for_client'),
    path('clients/<int:client_id>/cars/<int:car_id>/edit/', edit_car_for_client, name='edit_car_for_client'),
    path('get-models-for-brand/', get_models_for_brand, name='get_models_for_brand'),
    # إدارة شركات الصنع
    path('brands/', brands_list, name='brands_list'),
    path('brands/add/', add_brand, name='add_brand'),
    path('brands/<int:brand_id>/edit/', edit_brand, name='edit_brand'),
    path('brands/<int:brand_id>/delete/', delete_brand, name='delete_brand'),
    path('brands/bulk-delete/', brands_bulk_delete, name='brands_bulk_delete'),
    # إدارة الموديلات
    path('', include(('cars.urls', 'cars'), namespace='cars')),
    path('invoices/', include(('invoices.urls', 'invoices'), namespace='invoices')),
    path('models/', models_list, name='models_list'),
    path('models/add/', add_model, name='add_model'),
    path('models/<int:model_id>/edit/', edit_model, name='edit_model'),
    path('models/<int:model_id>/delete/', delete_model, name='delete_model'),
    path('models/bulk-delete/', models_bulk_delete, name='models_bulk_delete'),
    # تسجيل المستخدمين
    path('users/', include('users.urls')),
    # include Django auth URLs for password reset/confirm views
        # override password_change to clear force flag after change
        path('accounts/password_change/', AdminForcedPasswordChangeView.as_view(), name='password_change'),
        path('accounts/force_password_change/', force_password_change, name='force_password_change'),
        path('accounts/', include('django.contrib.auth.urls')),
    # الحجوزات
    path('bookings/', include('bookings.urls')),
    # Suppliers
    path('suppliers/', suppliers_list, name='suppliers_list'),
    path('suppliers/json/', suppliers_search_json, name='suppliers_json'),
    path('suppliers/add/', add_supplier, name='add_supplier'),
    path('suppliers/<int:supplier_id>/edit/', edit_supplier, name='edit_supplier'),
    path('suppliers/<int:supplier_id>/delete/', delete_supplier, name='delete_supplier'),
    # Bills (Purchases)
    path('bills/', include(('bills.urls', 'bills'))),
    # Reset pagination helpers (redirect to base list pages without query params)
    path('bills/reset-pagination/', lambda req: redirect('/bills/'), name='bills_reset_pagination'),
    # Vendor payments routes (list and add) - explicit so add uses vendor payments view
    path('vendors/payments/', vendor_payments_list, name='vendor_payments_list'),
    path('vendors/payments/add/', add_vendor_payment, name='vendor_payments_add'),
    path('vendors/payments/view/<int:payment_id>/', vendor_payment_detail, name='vendor_payment_detail'),
    path('vendors/payments/delete/', delete_vendor_payments, name='vendor_payments_delete'),
    path('vendors/payments/reset-pagination/', lambda req: redirect('/vendors/payments/'), name='vendor_payments_reset_pagination'),
    # Inventory / Items
    path('inventory/', inventory_list, name='inventory'),
    path('inventory/json/', inventory_search_json, name='inventory_json'),
    path('inventory/add/', add_part, name='inventory_add'),
    path('inventory/<int:part_id>/edit/', edit_part, name='inventory_edit'),
    path('inventory/bulk-delete/', inventory_bulk_delete, name='inventory_bulk_delete'),
]