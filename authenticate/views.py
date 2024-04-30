import json
from django.utils import timezone

from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from Gas import settings
from .renderers import UserJSONRenderer
from .serializers import (
    LoginSerializer, RegistrationSerializer, UserSerializer,
)
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import PasswordResetCode, User
import json

class RegistrationAPIView(APIView):
    renderer_classes = (UserJSONRenderer,)
    serializer_class = RegistrationSerializer

    def post(self, request):
        user = request.data.get('user', {})

        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = LoginSerializer

    def post(self, request):
        user = request.data.get('user', {})

        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class UserRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = UserSerializer

    def retrieve(self, request, *args, **kwargs):
        serializer = self.serializer_class(request.user)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        serializer_data = request.data.get('user', {})

        serializer = self.serializer_class(
            request.user, data=serializer_data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

@csrf_exempt
def generate_code(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        email = data.get('email')
        if email:
            PasswordResetCode.objects.filter(email=email).delete()
            code = PasswordResetCode.generate_code()
            PasswordResetCode.objects.create(email=email, code=code)
            send_mail(
                'Код для сброса пароля',
                f'Ваш код для сброса пароля: {code}',
                'FillSwift.com',
                [email],
                fail_silently=False,
            )
            return JsonResponse({'message': 'Код для сброса пароля отправлен на ваш адрес электронной почты.'})
        else:
            return JsonResponse({'error': 'Адрес электронной почты не указан.'}, status=400)
    else:
        return JsonResponse({'error': 'Метод запроса не поддерживается.'}, status=405)


@csrf_exempt
def reset_password(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        email = data.get('email')
        new_password = data.get('new_password')

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
        except User.DoesNotExist:
            return JsonResponse({'error': 'Пользователь с таким email не найден.'}, status=400)

        return JsonResponse({'message': 'Пароль успешно изменен.'})
    else:
        return JsonResponse({'error': 'Метод запроса не поддерживается.'}, status=405)

@csrf_exempt
def verify_code(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        email = data.get('email')
        code = data.get('code')
        new_password = data.get('new_password')

        try:
            reset_code = PasswordResetCode.objects.get(email=email, code=code)
        except PasswordResetCode.DoesNotExist:
            return JsonResponse({'error': 'Неверный код для сброса пароля.'}, status=400)

        if (timezone.now() - reset_code.created_at).seconds > 3600:
            reset_code.delete()
            return JsonResponse({'error': 'Срок действия кода истек.'}, status=400)

        return reset_password(request)

    else:
        return JsonResponse({'error': 'Метод запроса не поддерживается.'}, status=405)