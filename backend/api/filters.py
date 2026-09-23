import django_filters
from rest_framework import filters

from recipes.models import Favorite, Recipe, ShoppingCart, Tag
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
        if not value:
            return queryset

        request = getattr(self, 'request', None)
        if not request or not request.user.is_authenticated:
            return queryset.none()

        recipe_ids = Favorite.objects.filter(
            user=request.user).values_list('recipe_id', flat=True)
        return queryset.filter(id__in=recipe_ids)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            recipe_ids = ShoppingCart.objects.filter(
                user=self.request.user).values_list('recipe_id', flat=True)
            return queryset.filter(id__in=recipe_ids)
        return queryset


class IngredientSearchFilter(filters.SearchFilter):
    """Фильтрация для ингредиентов."""

    search_param = 'name'
