from django.shortcuts import redirect
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet


def redirect_to_recipe(request, pk):
    return redirect(f'https://foodgramcat.hopto.org/recipes/{pk}')


router = DefaultRouter()
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('s<int:pk>/', redirect_to_recipe, name='short_link'),
    path('', include(router.urls)),
]
