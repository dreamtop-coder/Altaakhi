from django.urls import path
from . import views

urlpatterns = [
    path("", views.bookings_list, name="bookings_list"),
    path("add/", views.booking_create, name="booking_create"),
    path("edit/<int:booking_id>/", views.booking_edit, name="booking_edit"),
    path("delete/<int:booking_id>/", views.booking_delete, name="booking_delete"),
    path("car-info/", views.booking_car_info_ajax, name="booking_car_info_ajax"),
    path(
        "start-maintenance/<int:booking_id>/",
        views.booking_start_maintenance,
        name="booking_start_maintenance",
    ),
]
