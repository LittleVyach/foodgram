from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Настройка отображения пользователей."""

    list_display = (
        'id', 'email', 'username', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'username')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
