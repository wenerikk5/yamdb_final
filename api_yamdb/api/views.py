from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import filters, status, viewsets
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from reviews.models import (
    CustomUser, Genre, Category, Title, Review)
from .permissions import (
    IsAdmin, IsAdminUserOrReadOnly, IsAuthorAdminModeratorOrReadOnly)
from .mixins import CreateDestroyListMixin
from .serializers import (SignUpSerializer, CustomUserSerializer,
                          AccountSerializer, CategorySerializer,
                          GenreSerializer, TitleReadSerializer,
                          TitleWriteSerializer, TokenSerializer,
                          ReviewSerializer, CommentSerializer)
from .filters import TitleFilter
from .utils import create_confirmation_code, send_email, get_token_for_user


@api_view(['POST'])
@permission_classes([AllowAny])
def user_signup(request):
    """Регистрация пользователя и отправка кода подтверждения на почту."""

    serializer = SignUpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data['username']
    email = serializer.validated_data['email'].lower()
    confirmation_code = create_confirmation_code()

    try:
        user, created = CustomUser.objects.get_or_create(
            username=username,
            email=email,
            defaults={'confirmation_code': confirmation_code}
        )
    except IntegrityError:
        return Response(
            'Пользователь с такими именем или почтой уже существует.',
            status=status.HTTP_400_BAD_REQUEST
        )

    if not created:
        confirmation_code = user.confirmation_code

    send_email(username, email, confirmation_code)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def user_auth(request):
    """Получение юзером токена."""

    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = get_object_or_404(
        CustomUser,
        username=serializer.validated_data['username']
    )
    if serializer.validated_data[
        'confirmation_code'
    ] != user.confirmation_code:
        return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
    response = get_token_for_user(user)
    return Response(response, status=status.HTTP_200_OK)


class UsersViewSet(viewsets.ModelViewSet):
    """Обработка профиля пользователя."""

    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)
    permission_classes = (IsAdmin,)
    lookup_field = 'username'

    @action(
        methods=['GET', 'PATCH'],
        detail=False,
        permission_classes=(IsAuthenticated,),
        serializer_class=AccountSerializer
    )
    def me(self, request):
        """Получение и изменение данных в профиле пользователя."""

        if self.request.method != 'PATCH':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)

        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class CategoryGenreViewSet(CreateDestroyListMixin, viewsets.GenericViewSet):
    """Базовый класс для CategoryViewSet и GenreViewSet."""

    permission_classes = (IsAdminUserOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class CategoryViewSet(CategoryGenreViewSet):
    """Обработка запроса к категориям."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GenreViewSet(CategoryGenreViewSet):
    """Обработка запроса к жанрам."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class TitleViewSet(viewsets.ModelViewSet):
    """Обработка запросов к произведениям."""

    queryset = Title.objects.all()
    # serializer_class = TitleWriteSerializer
    ordering = ['-rating', 'name']
    permission_classes = (IsAdminUserOrReadOnly,)
    filterset_class = TitleFilter

    def create(self, request, *args, **kwargs):
        genre = request.data.pop('genre')
        # to pass validation for genre:
        request.data['genre'] = [{"name": "name", "slug": "slug"}]
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer, genre)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer, data):
        serializer.save(genre=data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if 'genre' in request.data.keys():
            genre = request.data.pop('genre')
            request.data['genre'] = [{"name": "name", "slug": "slug"}]
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update2(serializer, genre)
        else:
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update1(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_update1(self, serializer):
        """Если нет переданного жанра."""
        serializer.save()

    def perform_update2(self, serializer, data):
        """Если обновляется жанр."""
        serializer.save(genre=data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от типа запроса."""
        if self.action in ('list', 'retrieve'):
            return TitleReadSerializer
        return TitleWriteSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """Обработка зарпосов к обзорам."""

    serializer_class = ReviewSerializer
    permission_classes = (
        IsAuthenticatedOrReadOnly,
        IsAuthorAdminModeratorOrReadOnly,
    )

    def get_title(self):
        """Получает из запроса объект Title."""
        return get_object_or_404(Title, id=self.kwargs.get('title_id'))

    def perform_create(self, serializer):
        """Создание обзора к произведению."""
        serializer.save(author=self.request.user, title=self.get_title())

    def get_queryset(self):
        """Возращает список обзоров к произведению."""
        return self.get_title().reviews.all()


class CommentViewSet(viewsets.ModelViewSet):
    """Обработка зарпосов к комментариям."""

    serializer_class = CommentSerializer
    permission_classes = (
        IsAuthenticatedOrReadOnly,
        IsAuthorAdminModeratorOrReadOnly,
    )

    def get_review(self):
        """Получает из запроса объект Review."""
        return get_object_or_404(
            Review,
            title_id=self.kwargs.get('title_id'),
            pk=self.kwargs.get('review_id')
        )

    def perform_create(self, serializer):
        """Создание комментария к обзору."""
        serializer.save(author=self.request.user,
                        review_id=self.get_review().id)

    def get_queryset(self):
        """Возращает список комментариев к обзору."""
        return self.get_review().comments.all()
