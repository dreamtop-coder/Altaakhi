from django.urls import path

from services.views_services_custom import services_edit, services_delete
from services.views import services_list, services_parts
from services.views import services_autocomplete
from services.views import services_add

urlpatterns = [
    path("services/", services_list, name="services_list"),
    path("services/<int:service_id>/edit/", services_edit, name="services_edit"),
    path("services/<int:service_id>/delete/", services_delete, name="services_delete"),
    path("services/add/", services_add, name="services_add"),
    path("services/<int:service_id>/parts/", services_parts, name="services_parts"),
    path("services-autocomplete/", services_autocomplete, name="services_autocomplete"),
]
