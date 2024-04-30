import jwt
from jwt import ExpiredSignatureError, InvalidSignatureError
from django.conf import settings
from rest_framework import authentication, exceptions
from .models import User

class JWTAuthentication(authentication.BaseAuthentication):
    authentication_header_prefix = 'Token'

    def authenticate(self, request):
        request.user = None

        auth_header = authentication.get_authorization_header(request).split()
        auth_header_prefix = self.authentication_header_prefix.lower()

        if not auth_header:
            return None

        if len(auth_header) == 1:
            return None

        elif len(auth_header) > 2:
            return None

        prefix = auth_header[0].decode('utf-8')
        token = auth_header[1].decode('utf-8')

        if prefix.lower() != auth_header_prefix:
            return None

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user = User.objects.get(pk=payload['id'])
            if not user.is_active:
                raise exceptions.AuthenticationFailed('Данный пользователь деактивирован.')
        except (ExpiredSignatureError, InvalidSignatureError):
            raise exceptions.AuthenticationFailed('Ошибка аутентификации. Неверная подпись токена.')
        except jwt.DecodeError:
            raise exceptions.AuthenticationFailed('Ошибка аутентификации. Невозможно декодировать токен.')
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('Пользователь соответствующий данному токену не найден.')

        return (user, token)
