from django.urls import path
from . import views
from .views import delete_invoice, invoices_print_list

urlpatterns = [
    path("print/", invoices_print_list, name="invoices_print_list"),
    path("print/<int:invoice_id>/", views.print_invoice, name="print_invoice"),
    path("account-statement/", views.account_statement_view, name="account_statement"),
    path(
        "account-statement/print/",
        views.account_statement_print_view,
        name="account_statement_print",
    ),
    path("", views.invoices_list, name="invoices_list"),
    path("edit/<int:invoice_id>/", views.edit_invoice, name="edit_invoice"),
    path("pay/<int:car_id>/", views.pay_invoice, name="pay_invoice"),
    path(
        "pay/invoice/<int:invoice_id>/",
        views.pay_invoice_by_id,
        name="pay_invoice_by_id",
    ),
    path("payments/", views.payments_list, name="payments_list"),
    path("due/", views.invoices_due_list, name="invoices_due_list"),
    path("payments/<int:payment_id>/edit/", views.edit_payment, name="edit_payment"),
    path("delete/<int:invoice_id>/", delete_invoice, name="delete_invoice"),
    path(
        "edit-records/<int:invoice_id>/",
        views.edit_invoice_records,
        name="edit_invoice_records",
    ),
]
