from django.urls import path
from . import views

urlpatterns = [
    path("", views.suppliers_list, name="suppliers_list"),
    path("add/", views.add_supplier, name="add_supplier"),
    path("<int:supplier_id>/", views.supplier_detail, name="supplier_detail"),
    path("<int:supplier_id>/delete/", views.delete_supplier, name="delete_supplier"),
    # items CRUD
    path("items/", views.items_list, name="items_list"),
    path("items/add/", views.add_item, name="add_item"),
    path("items/<int:item_id>/edit/", views.edit_item, name="edit_item"),
    path("items/<int:item_id>/delete/", views.delete_item, name="delete_item"),
    path("parts-autocomplete/", views.parts_autocomplete, name="parts_autocomplete"),
    path("parts-list/", views.parts_list, name="parts_list"),
    path("purchases/", views.purchases_list, name="purchases_list"),
    path("purchases/<int:purchase_id>/edit/", views.edit_purchase, name="edit_purchase"),
    path("purchases/<int:purchase_id>/delete/", views.delete_purchase, name="delete_purchase"),
]
