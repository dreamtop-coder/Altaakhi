from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from .views import dashboard_summary, revenue_monthly_ajax
from clients.views import clients_list
from clients.views import add_client, delete_client, client_detail, edit_client
from cars.views import cars_ajax_filter, start_maintenance
from cars.views_add import add_car_for_client, get_models_for_brand
from cars.brand_views import (
from cars.dashboard import cars_dashboard



    brands_list,
    add_brand,
    edit_brand,
    delete_brand,
    models_list,
    add_model,
    edit_model,
    delete_model,
)


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect("dashboard/")
    else:
        return redirect("/users/login/")


urlpatterns = [
    path("", root_redirect),
    path("admin/", admin.site.urls),
    path("dashboard/", dashboard_summary, name="dashboard"),
    path(
        "dashboard/revenue_monthly_ajax/",
        revenue_monthly_ajax,
        name="revenue_monthly_ajax",
    ),
    path("clients/", clients_list, name="clients_list"),
    path("clients/add/", add_client, name="add_client"),
    path("clients/delete/<int:client_id>/", delete_client, name="delete_client"),
    path("clients/<int:client_id>/", client_detail, name="client_detail"),
    path("clients/<int:client_id>/edit/", edit_client, name="edit_client"),
    path("cars/ajax/filter/", cars_ajax_filter, name="cars_ajax_filter"),
    path(
        "cars/start_maintenance/<int:car_id>/",
        start_maintenance,
        name="start_maintenance",
    ),  # أضف هذا السطر
    path("cars/dashboard/", cars_dashboard, name="cars_dashboard"),
    path(
        "clients/<int:client_id>/add_car/",
        add_car_for_client,
        name="add_car_for_client",
    ),
    path("get-models-for-brand/", get_models_for_brand, name="get_models_for_brand"),
    # إدارة شركات الصنع
    path("brands/", brands_list, name="brands_list"),
    path("brands/add/", add_brand, name="add_brand"),
    path("brands/<int:brand_id>/edit/", edit_brand, name="edit_brand"),
    path("brands/<int:brand_id>/delete/", delete_brand, name="delete_brand"),
    # إدارة الموديلات
    path("", include(("cars.urls", "cars"), namespace="cars")),
    path("", include("services.urls")),
    path("invoices/", include("invoices.urls")),
    path("models/", models_list, name="models_list"),
    path("models/add/", add_model, name="add_model"),
    path("models/<int:model_id>/edit/", edit_model, name="edit_model"),
    path("models/<int:model_id>/delete/", delete_model, name="delete_model"),
    # تسجيل المستخدمين
    path("users/", include("users.urls")),
    # الحجوزات
    path("bookings/", include("bookings.urls")),
]
