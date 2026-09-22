from django.contrib import admin

from .models import (
    Tag, Ingredient, Recipe, RecipeIngredient, Favorite, ShoppingCart, Follow
)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'color')
    search_fields = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'favorites_count')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags',)
    inlines = (RecipeIngredientInline,)

    @admin.display(description='В избранном (раз)')
    def favorites_count(self, obj):
        return obj.favorites.count()


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__email', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__email', 'recipe__name')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    search_fields = ('user__email', 'author__email')
