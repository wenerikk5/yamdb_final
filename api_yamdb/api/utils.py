import random

from django.core.mail import EmailMessage
from rest_framework_simplejwt.tokens import AccessToken

from api_yamdb.settings import (CONFIRMATION_CODE_CHARACTERS,
                                CONFIRMATION_CODE_LENGTH)


def create_confirmation_code():
    """Создание кода подтверждения."""

    confirmation_code = "".join(
        random.choice(CONFIRMATION_CODE_CHARACTERS)
        for _ in range(CONFIRMATION_CODE_LENGTH)
    )
    return confirmation_code


def send_email(name, email, confirmation_code):
    """Отправка пользователю в консоль письма с кодом подтверждения."""
    print("=====SEND_EMAIL=====")

    mail = EmailMessage(
        'Регистрация на сайте.',
        f'Здравствуйте, {name}. Ваш код подтверждения: {confirmation_code}',
        to=[email]
    )
    mail.send()


def get_token_for_user(user):
    """Получение токена авторизации."""

    access = AccessToken.for_user(user)
    return {'token': str(access)}
