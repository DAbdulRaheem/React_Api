# users/urls.py
from django.urls import path
from . import views
from .views import (
    register_user, login_user,
    AdminUserListView, AdminUserRoleUpdateView, UserCountView
)

urlpatterns = [
    # Auth APIs (5.1)
    path('auth/register/', register_user, name='register'),
    path('auth/login/', login_user, name='login'),
    
    # Admin APIs (5.2)
    path("auth/admin/register/", views.register_admin, name="admin-register"),
    path('auth/admin/login/', views.admin_login, name="admin-login"),
    path('admin/users/', AdminUserListView.as_view(), name='admin-user-list'),
    path('admin/users/<int:pk>/role/', AdminUserRoleUpdateView.as_view(), name='admin-user-role-update'),
    path('admin/users/count/', views.UserCountView.as_view(), name='user-count'),
]