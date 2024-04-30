from django.urls import path
from .views import (
    LoginAPIView, RegistrationAPIView, UserRetrieveUpdateAPIView, generate_code, verify_code, reset_password
)

app_name = 'authentication'
urlpatterns = [
    path('user', UserRetrieveUpdateAPIView.as_view()),
    path('users/', RegistrationAPIView.as_view()),
    path('users/login/', LoginAPIView.as_view()),
    path('reset-password/generate-code/', generate_code, name='generate_code'),
    path('reset-password/verify-code/', verify_code, name='verify_code'),
    path('reset-password/reset/', reset_password, name='reset_password'),
]