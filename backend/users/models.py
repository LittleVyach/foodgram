from django.contrib.auth.models import AbstractUser
from django.db import models

from api.constants import EMAIL_MAX_LENGTH, USERNAME_MAX_LENGTH
from api.validators import validate_username


class User(AbstractUser):
    """Кастомная модель пользователя."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    username = models.CharField(
        'Уникальный юзернейм',
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=(validate_username,)
    )
    email = models.EmailField(
        'Адрес электронной почты',
        max_length=EMAIL_MAX_LENGTH,
        unique=True
    )
    first_name = models.CharField(
        'Имя',
        max_length=USERNAME_MAX_LENGTH,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=USERNAME_MAX_LENGTH,
    )
    avatar = models.ImageField(
        'Картинка, закодированная в Base64',
        upload_to='users/',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.email
