# users/permissions.py
from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Allows access only to Admin users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'ADMIN')

class IsAuthorOrAdmin(permissions.BasePermission):
    """
    Allows access to Admin users, or the Author of the post.
    """
    def has_object_permission(self, request, view, obj):
        # Admins can do anything
        if request.user.role == 'ADMIN':
            return True
        
        # Authors can only modify their own objects (posts)
        if request.method in permissions.SAFE_METHODS:
            return True # Authors can view their own posts
            
        # For PUT/DELETE, check if the request user is the post author
        return obj.author == request.user

class IsAuthor(permissions.BasePermission):
    """
    Allows access only to Author users.
    """
    def has_permission(self, request, view):
        # Authors and Admins are allowed in Author APIs, but Admin has separate APIs
        return bool(request.user and request.user.is_authenticated and (request.user.role == 'AUTHOR' or request.user.role == 'ADMIN'))