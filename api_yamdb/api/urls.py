from django.urls import include, path
from rest_framework.routers import DefaultRouter
from api.views import (CategoryViewSet, GenreViewSet,
                       TitleViewSet, UsersViewSet,
                       ReviewViewSet, CommentViewSet,
                       user_signup, user_auth)

app_name = 'api'

router_v1 = DefaultRouter()

router_v1.register(r'categories', CategoryViewSet, basename='category')
router_v1.register(r'genres', GenreViewSet, basename='genre')
router_v1.register(r'titles', TitleViewSet, basename='title')
router_v1.register(r'users', UsersViewSet, basename='user')
router_v1.register(
    r'titles/(?P<title_id>[\d]+)/reviews',
    ReviewViewSet,
    basename='review'
)
router_v1.register(
    r'titles/(?P<title_id>[\d]+)/reviews/(?P<review_id>[\d]+)/comments',
    CommentViewSet,
    basename='comment'
)

urlpatterns = [
    path('v1/auth/signup/', user_signup),
    path('v1/auth/token/', user_auth),
    path('v1/', include(router_v1.urls)),
]
