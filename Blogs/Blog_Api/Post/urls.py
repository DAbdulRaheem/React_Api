# posts/urls.py
from django.urls import path
from .views import (
    PublicPostListView, PublicPostDetailView,
    AuthorPostListCreateView, AuthorPostRetrieveUpdateDestroyView,
    AdminPendingPostListView, AdminPostStatusUpdateView, AdminPostDeleteView
)

urlpatterns = [
    # Public APIs (5.4)
    path('public/posts/', PublicPostListView.as_view(), name='public-post-list'),
    path('public/posts/<int:id>/', PublicPostDetailView.as_view(), name='public-post-detail'),
    
    # Author APIs (5.3)
    path('posts/', AuthorPostListCreateView.as_view(), name='author-post-create'), # Create post
    path('posts/my-posts/', AuthorPostListCreateView.as_view(), name='author-my-posts'), # List my posts
    path('posts/<int:id>/', AuthorPostRetrieveUpdateDestroyView.as_view(), name='author-post-detail-edit-delete'),

    # Admin APIs (5.2)
    path('admin/posts/pending/', AdminPendingPostListView.as_view(), name='admin-pending-posts'),
    path('admin/posts/<int:id>/status/', AdminPostStatusUpdateView.as_view(), name='admin-post-status-update'),
    path('admin/posts/<int:id>/', AdminPostDeleteView.as_view(), name='admin-post-delete'),
]