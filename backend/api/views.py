from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)

from .filters import IngredientSearchFilter, RecipeFilter
from .pagination import LimitPageNumberPagination
from .permissions import IsAdminOrReadOnly, IsAuthenticatedAuthorOrReadOnly
from .serializers import (FavoriteSerializer, FollowListSerializer,
                          FollowSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeReadSerializer,
                          ShoppingCartSerializer, TagSerializer)

User = get_user_model()


class ReadOnlyPaginationViewSet(viewsets.ReadOnlyModelViewSet):
    """Базовый вьюсет для тегов и ингредиентов."""

    pagination_class = None


class TagViewSet(ReadOnlyPaginationViewSet):
    """Вьюсет для тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class IngredientViewSet(ReadOnlyPaginationViewSet):
    """Вьюсет для ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов."""

    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthenticatedAuthorOrReadOnly,)
    pagination_class = LimitPageNumberPagination

    def get_queryset(self):
        user = self.request.user
        queryset = Recipe.objects.all()
        if not user.is_authenticated:
            return queryset

        queryset = queryset.annotate(
            is_favorited=Exists(
                Favorite.objects.filter(user=user, recipe=OuterRef('pk'))
            ),
            is_in_shopping_cart=Exists(
                ShoppingCart.objects.filter(user=user, recipe=OuterRef('pk'))
            ),
        )

        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited is not None:
            if is_favorited in {'1', 'true', 'True'}:
                queryset = queryset.filter(is_favorited=True)
            elif is_favorited in {'0', 'false', 'False'}:
                queryset = queryset.filter(is_favorited=False)

        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart')
        if is_in_shopping_cart is not None:
            if is_in_shopping_cart in {'1', 'true', 'True'}:
                queryset = queryset.filter(is_in_shopping_cart=True)
            elif is_in_shopping_cart in {'0', 'false', 'False'}:
                queryset = queryset.filter(is_in_shopping_cart=False)

        return queryset

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeCreateSerializer

    def add_to(self, serializer_class, request, pk):
        serializer = serializer_class(
            data={'recipe': pk},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_from(self, serializer_class, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        serializer = serializer_class(context={'request': request})
        serializer.remove(recipe)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return self.add_to(FavoriteSerializer, request.user, pk)
        return self.remove_from(FavoriteSerializer, request.user, pk)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            return self.add_to(ShoppingCartSerializer, request.user, pk)
        return self.remove_from(ShoppingCartSerializer, request.user, pk)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated),
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        )
        shopping_list = []
        for item in ingredients:
            name = item['ingredient__name']
            unit = item['ingredient__measurement_unit']
            amount = item['total_amount']
            shopping_list.append(f'{name} ({unit}) - {amount}')

        text_file = '\n'.join(shopping_list)

        response = HttpResponse(
            text_file, content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response

    @action(
        detail=True,
        permission_classes=(AllowAny,),
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        path = f'/s{recipe.id}/'
        short_link = request.build_absolute_uri(path)
        return Response({'short-link': short_link})


class UserViewSet(DjoserUserViewSet):
    """Вьюсет для пользователя."""

    queryset = User.objects.all()
    pagination_class = LimitPageNumberPagination

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = self.get_object()
        serializer = FollowSerializer(
            data={},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        if request.method == 'POST':
            serializer.save(user=user)
            return Response(
                FollowListSerializer(
                    author, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )

        if request.method == 'DELETE':
            user.follower.filter(author=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        authors = User.objects.filter(following__user=request.user)
        pages = self.paginate_queryset(authors)
        serializer = FollowListSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar'
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = self.get_serializer(
                user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        if request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
