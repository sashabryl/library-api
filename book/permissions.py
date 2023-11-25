from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_staff or request.method in SAFE_METHODS)


class IsAdminOrAuthenticatedOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(
            request.user.is_staff or
            (request.user.is_authenticated and obj.user == request.user)
        )
