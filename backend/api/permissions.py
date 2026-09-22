from rest_framework import permissions


class IsAuthor(permissions.BasePermission):
    """Разрешение только авторам."""

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешает чтение всем пользователям,
    но изменение/удаление — только автору объекта.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """Разрешение только админам."""

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or (request.user.is_authenticated and request.user.is_staff)
        )
