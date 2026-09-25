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
        fields = ('tags', 'author')


class IngredientSearchFilter(filters.SearchFilter):
    """Фильтрация для ингредиентов."""

    search_param = 'name'
