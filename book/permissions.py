from rest_framework.permissions import BasePermission


class IsAdminOrListOnly(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_staff or view.action == "list")


class BorrowingIsAdminOrAuthenticatedOwner(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user.is_staff
            or (request.user.is_authenticated and obj.user == request.user)
        )


class PaymentIsAdminOrAuthenticatedOwner(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user.is_staff
            or (
                request.user.is_authenticated
                and obj.borrowing.user == request.user
            )
        )
