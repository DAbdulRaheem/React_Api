# react_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path("api/auth/register/", views.register, name="register"),
    path("api/auth/login/", views.login, name="login"),

    # Public
    path("api/public/posts/", views.public_posts, name="public_posts"),
    path("api/public/posts/<int:post_id>/", views.public_post_detail, name="public_post_detail"),

    # Author
    path("api/posts/", views.create_post, name="create_post"),
    path("api/posts/<int:post_id>/", views.edit_post, name="edit_post"),  # PUT
    path("api/posts/<int:post_id>/delete/", views.delete_post, name="delete_post"),  # DELETE

    # Admin
    path("api/admin/users/", views.admin_list_users, name="admin_list_users"),
    path("api/admin/users/<int:user_id>/role/", views.admin_update_user_role, name="admin_update_user_role"),
    path("api/admin/posts/<int:post_id>/status/", views.admin_update_post_status, name="admin_update_post_status"),
    path("api/admin/posts/<int:post_id>/delete/", views.admin_delete_post, name="admin_delete_post"),
]
