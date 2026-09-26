from rest_framework import permissions


class IsAuthenticatedAuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """
    Разрешает чтение всем.

    Создание — аутентифицированным пользователям.
    Изменение/удаление — только автору объекта.
    """

    def has_object_permission(self, request, view, recipe):
        return (
            request.method in permissions.SAFE_METHODS
            or recipe.author == request.user
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """Разрешение только админам."""

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or (request.user.is_authenticated and request.user.is_staff)
        )
