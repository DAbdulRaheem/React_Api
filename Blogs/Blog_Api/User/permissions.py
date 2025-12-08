from rest_framework.permissions import BasePermission

class IsAdminUser(BasePermission):
    """Allow only users with role = ADMIN"""
    def has_permission(self, request, view):
        return request.user and request.user.role == "ADMIN"


class IsAuthor(BasePermission):
    """Allow only users with role = AUTHOR"""
    def has_permission(self, request, view):
        return request.user and request.user.role == "AUTHOR"


class IsAuthorOrAdmin(BasePermission):
    """Allow only AUTHOR or ADMIN"""
    def has_permission(self, request, view):
        return (
            request.user
            and hasattr(request.user, 'role')
            and request.user.role in ["AUTHOR", "ADMIN"]
        )
