from django.urls import path

from .views import register_user, login_user, logout_user
from .views import list_users, create_user, edit_user, toggle_user_active, reset_user_password, audit_logs, unlock_user, users_json

urlpatterns = [
    path('register/', register_user, name='register_user'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),

    # Admin user management (restricted to staff)
    path('admin/users/', list_users, name='users_list'),
    path('admin/users/create/', create_user, name='users_create'),
    path('admin/users/<int:pk>/edit/', edit_user, name='users_edit'),
    path('admin/users/<int:pk>/toggle/', toggle_user_active, name='users_toggle'),
    path('admin/users/<int:pk>/reset_password/', reset_user_password, name='users_reset_password'),
    path('admin/users/<int:pk>/unlock/', unlock_user, name='users_unlock'),
    path('admin/users/audit/', audit_logs, name='users_audit_logs'),
    path('admin/users/json/', users_json, name='users_json'),
]
