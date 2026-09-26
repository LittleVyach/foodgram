import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers

from recipes.models import (Favorite, Follow, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для обработки картинок."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')
        return super().to_internal_value(data)


class UserRegistrationSerializer(UserCreateSerializer):
    """Сериализатор для регистрации пользователя."""

    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'password', 'avatar'
        )

    def validate(self, attrs):
        validated_data = dict(attrs)
        validated_data.pop('re_password', None)
        return super().validate(validated_data)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода информации о пользователе."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.following.filter(user=request.user, author=obj).exists()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug', 'color')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class ReadRecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения ингредиентов внутри рецепта."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения (Get)."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = ReadRecipeIngredientSerializer(
        source='recipe_ingredients', many=True, read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        if hasattr(obj, 'is_favorited'):
            return obj.is_favorited
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        if hasattr(obj, 'is_in_shopping_cart'):
            return obj.is_in_shopping_cart
        return ShoppingCart.objects.filter(
            user=request.user, recipe=obj).exists()


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи ингредиентов."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = RecipeIngredientWriteSerializer(many=True)
    image = Base64ImageField()
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Recipe
        fields = (
            'id',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            'author',
        )

    def save_ingredients(self, recipe, ingredients_data):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount'],
            )
            for ingredient_data in ingredients_data
        )

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self.save_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('ingredients', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags_data is not None:
            instance.tags.set(tags_data)

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self.save_ingredients(instance, ingredients_data)
        return instance

    def to_representation(self, instance):
        """Возвращаем созданный рецепт через сериализатор чтения."""
        return RecipeReadSerializer(
            instance, context={'request': self.context.get('request')}
        ).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого отображения."""

    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe=obj).exists()


class BaseRecipeRelationSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для связи."""

    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def validate(self, data):
        user = self.context['request'].user
        recipe = data['recipe']

        if self.Meta.model.objects.filter(user=user, recipe=recipe).exists():
            error_message = getattr(
                self,
                'default_error_message',
                'Рецепт уже добавление в этот список!'
            )
            raise serializers.ValidationError({'errors': error_message})

        return data

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe, context={'request': self.context.get('request')}
        ).data

    def remove(self, recipe):
        user = self.context['request'].user
        deleted_count, _ = self.Meta.model.objects.filter(
            user=user, recipe=recipe
        ).delete()
        if deleted_count == 0:
            raise serializers.ValidationError(
                {'errors': 'Рецепта не было в этом списке!'}
            )


class FavoriteSerializer(BaseRecipeRelationSerializer):
    """Сериализатор для добавления и удаления в избранном."""

    default_error_message = 'Этот рецепт уже добавлен в избранное!'

    class Meta:
        model = Favorite
        fields = ('recipe', 'user')


class ShoppingCartSerializer(BaseRecipeRelationSerializer):
    """Сериализатор для добавления и удаления в корзине."""

    default_error_message = 'Этот рецепт уже добавлен в корзину!'

    class Meta:
        model = ShoppingCart
        fields = ('recipe', 'user')


class FollowListSerializer(UserSerializer):
    """Сериализатор для вывода авторов."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit') if request else None
        recipes = obj.recipes.all()

        if limit:
            try:
                recipes = recipes[: int(limit)]
            except (ValueError, TypeError):
                pass

        return RecipeShortSerializer(
            recipes, many=True, context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и удаления подписок."""

    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Follow
        fields = ('author',)

    def validate(self, data):
        user = self.context['request'].user
        author = data['author']

        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписываться на самого себя!'
            )

        if user.follower.filter(author=author).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя.'
            )

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        author = validated_data['author']
        return user.follower.create(author=author)

    def to_representation(self, instance):
        request = self.context.get('request')
        return FollowListSerializer(
            instance.author, context={'request': request}
        ).data
