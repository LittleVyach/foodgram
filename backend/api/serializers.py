import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers

from recipes.models import (
    Favorite,
    Follow,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag
)


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для обработки картинок."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для регистрации пользователя."""

    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'password', 'avatar'
        )


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода информации о пользователе."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Follow.objects.filter(user=request.user, author=obj).exists()


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
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)
    image = Base64ImageField()

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

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount'],
            )
        return recipe

    def to_representation(self, instance):
        """Возвращаем созданный рецепт через сериализатор чтения."""
        return RecipeReadSerializer(
            instance, context={'request': self.context.get('request')}
        ).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого отображения."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class BaseRecipeRelationSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для связи."""

    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def validate(self, data):
        user = self.context['request'].user
        recipe = data['recipe']

        if self.Meta.model.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(self.default_error_message)
        return data

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe, context={'request': self.context.get('request')}
        ).data


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


class FollowListSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода авторов."""

    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
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

    def get_is_subscribed(self, obj):
        return True


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и удаления подписок."""
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Follow
        fields = ('user', 'author')

    def validate(self, data):
        user = self.context['request'].user
        author = data['author']

        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписываться на самого себя!'
            )
        if Follow.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого автора.'
            )
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        return FollowListSerializer(
            instance.author, context={'request': request}
        ).data
