from django.urls import path
from . import views

from .views_add_maintenance import (
    add_maintenance_record,
    get_service_price,
    get_car_info,
)
from .views import cars_ajax_filter

urlpatterns = [
    path("cars/", views.cars_list, name="cars_list"),
    path("maintenance/", views.maintenance_list, name="maintenance_list"),
    path("maintenance/add/", add_maintenance_record, name="add_maintenance_record"),
    path(
        "maintenance/edit/<int:record_id>/",
        views.edit_maintenance_record,
        name="edit_maintenance_record",
    ),
    path(
        "maintenance/edit-fields/<int:record_id>/",
        views.edit_maintenance_record_fields,
        name="edit_maintenance_record_fields",
    ),
    path(
        "maintenance/delete/<int:record_id>/",
        views.delete_maintenance_record,
        name="delete_maintenance_record",
    ),
    path("get-service-price/", get_service_price, name="get_service_price"),
    path("get-car-info/", get_car_info, name="get_car_info"),
    path("cars/deliver/<int:car_id>/", views.deliver_car, name="deliver_car"),
    path("cars/start/<int:car_id>/", views.start_maintenance, name="start_maintenance"),
    path(
        "cars/finish/<int:car_id>/", views.finish_maintenance, name="finish_maintenance"
    ),
    # AJAX filter endpoint for dashboard car status
    path("cars/ajax/filter/", cars_ajax_filter, name="cars_ajax_filter"),
    path(
        "cars/ajax/bookings_clients/", views.bookings_clients, name="bookings_clients"
    ),
    path("get_done_count/", views.get_done_count, name="get_done_count"),
]
