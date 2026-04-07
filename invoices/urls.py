from django.urls import path
from . import views
from .views import delete_invoice, invoices_print_list

urlpatterns = [
    path('print/', invoices_print_list, name='invoices_print_list'),
    path('print/<int:invoice_id>/', views.print_invoice, name='print_invoice'),
    path('account-statement/', views.account_statement_view, name='account_statement'),
    path('account-statement/print/', views.account_statement_print_view, name='account_statement_print'),
    path('financial/', views.financial_management, name='financial_management'),
    path('json/charts/', views.charts_data, name='charts_data'),
    path('reports/', views.reports_view, name='reports_view'),
    path('json/reports/revenue/', views.reports_revenue_json, name='reports_revenue_json'),
    path('reports/export/revenue/csv/', views.reports_revenue_csv, name='reports_revenue_csv'),
    path('json/reports/aging/', views.reports_aging_json, name='reports_aging_json'),
    path('reports/export/aging/csv/', views.reports_aging_csv, name='reports_aging_csv'),
    path('', views.invoices_list, name='invoices_list'),
    path('add/', views.add_invoice, name='add_invoice'),
    path('edit/<int:invoice_id>/', views.edit_invoice, name='edit_invoice'),
    path('pay/<int:car_id>/', views.pay_invoice, name='pay_invoice'),
    path('pay/invoice/<int:invoice_id>/', views.pay_invoice_by_id, name='pay_invoice_by_id'),
    path('payments/', views.payments_list, name='payments_list'),
    path('payments/add/', views.add_payment, name='add_payment'),
    path('payments/client-invoices/<int:client_id>/', views.client_invoices_json, name='client_invoices_json'),
    path('json/invoice/<int:invoice_id>/', views.get_invoice_json, name='get_invoice_json'),
    path('bulk-delete/', views.bulk_delete_invoices, name='bulk_delete_invoices'),
    path('payments/<int:payment_id>/delete/', views.delete_payment, name='delete_payment'),
    path('due/', views.invoices_due_list, name='invoices_due_list'),
    path('payments/<int:payment_id>/edit/', views.edit_payment, name='edit_payment'),
    path('delete/<int:invoice_id>/', delete_invoice, name='delete_invoice'),
    path('edit-records/<int:invoice_id>/', views.edit_invoice_records, name='edit_invoice_records'),
    # Expenses
    path('expenses/', views.expenses_list, name='expenses_list'),
    path('expenses/add/', views.add_expense, name='add_expense'),
]
