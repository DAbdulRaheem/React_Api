# react_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # -------------------------------------------------
    # AUTH APIs
    # -------------------------------------------------
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),

    # -------------------------------------------------
    # PUBLIC POSTS (VIEWER accessible)
    # -------------------------------------------------
    path('public/posts/', views.public_posts, name='public_posts'),
    path('public/posts/<int:post_id>/', views.public_post_detail, name='public_post_detail'),

    # -------------------------------------------------
    # AUTHOR APIs (AUTHOR/ADMIN accessible)
    # -------------------------------------------------
    # Post CRUD for Authors
    path('author/posts/create/', views.create_post, name='create_post'),
    path('author/posts/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('author/posts/<int:post_id>/delete/', views.delete_post, name='delete_post'),

    # -------------------------------------------------
    # ADMIN APIs (ADMIN accessible)
    # -------------------------------------------------
    # User Management
    path('admin/users/', views.admin_list_users, name='admin_list_users'),
    path('admin/users/<int:user_id>/role/', views.admin_update_user_role, name='admin_update_user_role'),
    
    # Content Management
    path('admin/posts/<int:post_id>/status/', views.admin_update_post_status, name='admin_update_post_status'),
    path('admin/posts/<int:post_id>/delete/', views.admin_delete_post, name='admin_delete_post'), # ADMIN delete ANY post
]