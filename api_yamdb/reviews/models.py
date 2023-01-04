from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from .validators import (
    RegexUsernameValidator, validate_year, validate_username_not_me)


class CustomUser(AbstractUser):
    """Кастомная модель пользователей."""

    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'
    ROLES = (
        (USER, 'user'),
        (MODERATOR, 'moderator'),
        (ADMIN, 'amdin')
    )

    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[RegexUsernameValidator, validate_username_not_me]
    )
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    bio = models.TextField(
        'Биография',
        blank=True
    )
    role = models.CharField(
        "Роль",
        max_length=20,
        choices=ROLES,
        default=USER
    )
    email = models.EmailField(
        "Почта",
        max_length=254,
        unique=True
    )
    confirmation_code = models.CharField(
        "Код подтверждения",
        max_length=50,
        null=True
    )

    def is_admin(self):
        return self.role == self.ADMIN or self.is_staff

    def is_moderator(self):
        return self.role == self.MODERATOR


class CategoryGenreModel(models.Model):
    """Базовый класс для моделей Category и Genre."""

    name = models.TextField('Название', max_length=256)
    slug = models.SlugField(
        "Слаг",
        max_length=50,
        unique=True,
        db_index=True
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.name}'


class Genre(CategoryGenreModel):
    """Модель для жанров произведений."""

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'


class Category(CategoryGenreModel):
    """Модель для категорий произведений."""

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Title(models.Model):
    """Модель произведений."""

    name = models.TextField('Название произведения', db_index=True)
    description = models.TextField('Описание', null=True, blank=True)
    year = models.PositiveSmallIntegerField(
        'Год',
        validators=[validate_year, ]
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='titles',
        verbose_name='Категория'
    )
    genre = models.ManyToManyField(
        Genre,
        through='GenreTitle',
        blank=False,
        related_name='titles',
        verbose_name='Жанр'
    )

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'

    def __str__(self):
        return f'{self.name}, {self.year}'


class ReviewCommentModel(models.Model):
    """Базовый класс для моделей Review и Comment."""

    text = models.TextField(
        'Текст'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )

    class Meta:
        abstract = True
        ordering = ['-pub_date']


class Review(ReviewCommentModel):
    """Модель для отзывов."""

    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        verbose_name='Произведение'
    )
    score = models.PositiveSmallIntegerField(
        'Оценка',
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    FIELDS_INFO = (
        'Текст: {text};'
        'Автор: {author};'
        'Дата публикации: {pub_date};'
        'Произведение: {title};'
        'Оценка: {score}.'
    )

    def __str__(self):
        return self.FIELDS_INFO.format(
            text=self.text,
            author=self.author,
            pub_date=self.pub_date,
            title=self.title,
            score=self.score
        )

    class Meta(ReviewCommentModel.Meta):
        default_related_name = 'reviews'
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'title'],
                name='author_title_connection'
            )
        ]


class Comment(ReviewCommentModel):
    """Модель комментариев."""

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        verbose_name='Обзор'
    )

    FIELDS_INFO = (
        'Текст: {text};'
        'Дата публикации: {pub_date};'
        'Автор: {author};'
        'Обзор: {review}.'
    )

    def __str__(self):
        return self.FIELDS_INFO.format(
            text=self.text,
            pub_date=self.pub_date,
            author=self.author,
            review=self.review
        )

    class Meta(ReviewCommentModel.Meta):
        default_related_name = 'comments'
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'


class GenreTitle(models.Model):
    """Связывающая промежуточная таблица Жанр-Произведение."""

    genre = models.ForeignKey(
        Genre,
        on_delete=models.CASCADE
    )
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f'{self.genre} - {self.title}'
