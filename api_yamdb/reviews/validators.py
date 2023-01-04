from datetime import datetime

from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError


class RegexUsernameValidator(UnicodeUsernameValidator):
    """Валидация имени пользователя по допустимым символам."""

    regex = r'^[\w.@+-]+\z'


def validate_username_not_me(value):
    """Запрет на создание пользователя с username=me."""

    if value == 'me':
        raise ValidationError("Имя пользователя 'me' запрещено!")
    return value


def validate_year(value):
    """Проверка, что год выхода произведения не позднее текущего."""

    if value > datetime.now().year:
        raise ValidationError(f'{value} год еще не наступил!')
