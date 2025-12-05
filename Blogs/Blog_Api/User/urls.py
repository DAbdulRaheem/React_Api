# users/urls.py
from django.urls import path
from .views import (
    register_user, login_user,
    AdminUserListView, AdminUserRoleUpdateView
)

urlpatterns = [
    # Auth APIs (5.1)
    path('auth/register/', register_user, name='register'),
    path('auth/login/', login_user, name='login'),
    
    # Admin APIs (5.2)
    path('admin/users/', AdminUserListView.as_view(), name='admin-user-list'),
    path('admin/users/<int:pk>/role/', AdminUserRoleUpdateView.as_view(), name='admin-user-role-update'),
]