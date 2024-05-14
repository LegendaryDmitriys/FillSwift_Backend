from django.urls import path
from .views import (
    LoginAPIView, RegistrationAPIView, UserRetrieveUpdateAPIView, generate_code, verify_code, reset_password,
    UserListAPIView, UserDetailsRetrieveUpdateDestroyAPIView, reset_password_admin
)

app_name = 'authentication'
urlpatterns = [
    path('user', UserRetrieveUpdateAPIView.as_view(), name='user'),
    path('user-list', UserListAPIView.as_view(), name='user-list'),
    path('users/<int:id>/', UserDetailsRetrieveUpdateDestroyAPIView.as_view(), name='user-details'),
    path('users/', RegistrationAPIView.as_view(), name='registration'),
    path('users/login/', LoginAPIView.as_view()),
    path('reset-password/generate-code/', generate_code, name='generate_code'),
    path('reset-password-admin/', reset_password_admin, name='reset_password_admin'),
    path('reset-password/verify-code/', verify_code, name='verify_code'),
    path('reset-password/reset/', reset_password, name='reset_password'),

]