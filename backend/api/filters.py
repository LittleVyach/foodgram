import django_filters
from rest_framework import filters

from recipes.models import Recipe, Tag
from users.models import User


class RecipeFilter(django_filters.FilterSet):
    """Фильтрация для рецептов."""

    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )

    author = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    is_favorited = django_filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        request = getattr(self, 'request', None)
        if not request or not request.user.is_authenticated:
            return queryset.none()

        if value in (True, 'True', 'true', 1, '1'):
            return queryset.filter(favorite__user=request.user)
        elif value in (False, 'False', 0, '0'):
            return queryset.exclude(favorite__user=request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        request = getattr(self, 'request', None)
        if not request or not request.user.is_authenticated:
            return queryset.none()

        if value in (True, 'True', 'true', 1, '1'):
            return queryset.filter(shopping_cart__user=request.user)
        elif value in (False, 'False', 0, '0'):
            return queryset.exclude(shopping_cart__user=request.user)
        return queryset


class IngredientSearchFilter(filters.SearchFilter):
    """Фильтрация для ингредиентов."""

    search_param = 'name'
