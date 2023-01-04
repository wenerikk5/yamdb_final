from django.shortcuts import get_object_or_404
from rest_framework import serializers
from reviews.models import (
    CustomUser, Genre, Category, Title, GenreTitle, Review, Comment
)
from reviews.validators import (validate_username_not_me,
                                RegexUsernameValidator)


class GenreTitleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Genre
        fields = ('name', 'slug')


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра и создания пользователей админом."""

    class Meta:
        model = CustomUser
        fields = (
            'username',
            'email',
            'role',
            'first_name',
            'last_name',
            'bio'
        )


class AccountSerializer(CustomUserSerializer):
    """Сериализатор для просмотра юзером своего профиля."""

    class Meta(CustomUserSerializer.Meta):
        read_only_fields = ('role',)


class SignUpSerializer(serializers.Serializer):
    """Сериализатор для регистрации."""

    username = serializers.CharField(
        max_length=150,
        validators=[validate_username_not_me, RegexUsernameValidator]
    )
    email = serializers.EmailField(
        max_length=254,
        allow_blank=False,
        allow_null=False
    )


class TokenSerializer(serializers.Serializer):
    """Сериализатор для создания токенов."""

    username = serializers.CharField(
        max_length=150,
        validators=[validate_username_not_me, RegexUsernameValidator]
    )
    confirmation_code = serializers.CharField(max_length=50)


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для запросов по категориям."""

    class Meta:
        model = Category
        fields = ('name', 'slug',)


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор для запросов по жанрам."""

    class Meta:
        model = Genre
        fields = ('name', 'slug')


class TitleReadSerializer(serializers.ModelSerializer):
    """Сериализатор для безопасных запросов по произведениям."""

    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(many=True)
    rating = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Title
        fields = (
            'id',
            'name',
            'year',
            'description',
            'genre',
            'category',
            'rating'
        )
        read_only_fields = ('__all__',)

    def get_rating(self, obj):
        sum = 0
        count = 0

        for review in obj.reviews.all():
            sum += review.score
            count += 1

        if count == 0:
            return int(0)

        return int(sum / count)


class TitleWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления/изменения произведений."""

    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug'
    )

    genre = GenreSerializer(many=True)

    class Meta:
        model = Title
        fields = (
            'id',
            'name',
            'year',
            'description',
            'genre',
            'category',
        )

    def create(self, validated_data):
        """Создадим запись о новом произведении и внесем данные по жанрам.
        Если жанр новый - создадим новую запись в модели Жанра."""
        print("=====CREATE")
        genres = validated_data.pop('genre')

        title = Title.objects.create(**validated_data)

        for genre in genres:
            print("=====genre====")
            current_genre, status = Genre.objects.get_or_create(**genre)
            GenreTitle.objects.create(
                genre=current_genre,
                title=title
            )
        return title

    def update(self, instance, validated_data):
        """Изменим существующую запись произведения."""

        # Если изменяется категория произведения - удалим все
        # связанные записи в промежуточной таблице GenreTitle, и
        # заново создадим записи из переданных данных.
        if validated_data.get('genre', -1) != -1:

            # Найдем все существующие связанные жанры и удалим их
            # после создания новых (нужна валидация полученных данных).
            genre_items_to_delete = GenreTitle.objects.filter(
                title__id=instance.id
            )
            print("====GENRE ITEMS TO DELETE: ", genre_items_to_delete)

            # Непонятно почему без этой строчки все жанры
            # произведения удаляются.
            print('====Genre items to delete: ', len(genre_items_to_delete))

            # Создадим новые записи в таблице GenreTitle
            genres = validated_data.get('genre')
            for genre in genres:
                current_genre, status = Genre.objects.get_or_create(
                    name=genre['name'],
                    slug=genre['slug'])
                GenreTitle.objects.create(
                    genre=current_genre,
                    title=instance)

            # Если новые записи созданы успешно, то удаляем старые:
            if len(genre_items_to_delete) > 0:
                for item in genre_items_to_delete:
                    item.delete()

        instance.name = validated_data.get('name', instance.name)
        instance.year = validated_data.get('year', instance.year)
        instance.description = validated_data.get(
            'description',
            instance.description
        )
        instance.category = validated_data.get('category', instance.category)
        instance.save()

        return instance


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор для запросов по обзорам."""

    author = serializers.SlugRelatedField(
        slug_field='username', read_only=True)

    def validate(self, data):
        """Проверка, что у пользователя еще нет отзыва на это произведение."""

        if self.context.get('request').method != 'POST':
            return data
        print('=========Self.Context in Validation=======')
        print(f'self.context: {self.context}')
        title_id = self.context.get('view').kwargs.get('title_id')
        title = get_object_or_404(Title, id=title_id)
        user = self.context.get('request').user
        message = 'Вы уже оставляли отзыв на это произведение.'

        if Review.objects.filter(title=title, author=user).exists():
            raise serializers.ValidationError(message)
        return data

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'score', 'pub_date',)


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор для запросов по комментариям."""

    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date',)
