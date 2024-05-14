from rest_framework import serializers
from django.contrib.auth import authenticate

from .models import User


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True,
    )
    token = serializers.CharField(max_length=255, read_only=True)

    class Meta:
        model = User
        fields = ['email', 'lastname', 'firstname', 'username', 'password', 'token']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)



class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=255)
    username = serializers.CharField(max_length=255, read_only=True)
    password = serializers.CharField(max_length=128, write_only=True)
    token = serializers.CharField(max_length=255, read_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    operator =serializers.BooleanField(read_only=True)
    def validate(self, data):
        email = data.get('email', None)
        password = data.get('password', None)

        if email is None:
            raise serializers.ValidationError(
                'An email address is required to log in.'
            )

        if password is None:
            raise serializers.ValidationError(
                'A password is required to log in.'
            )

        user = authenticate(username=email, password=password)

        if user is None:
            raise serializers.ValidationError(
                'A user with this email and password was not found.'
            )


        if not user.is_active:
            raise serializers.ValidationError(
                'This user has been deactivated.'
            )


        return {
            'email': user.email,
            'username': user.username,
            'token': user.token,
            'is_staff': user.is_staff,
            'operator': user.operator
        }

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True,
        required=False
    )

    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'token', 'lastname', 'firstname', 'id', 'avatar', 'total_spent', 'total_refueled','operator')

        read_only_fields = ('token',)

    def create(self, validated_data):
        avatar = validated_data.pop('avatar', None)
        user = super().create(validated_data)
        if avatar:
            user.avatar = avatar
            user.save()
        return user

    def update(self, instance, validated_data):
        avatar = validated_data.pop('avatar', None)
        instance = super().update(instance, validated_data)
        if avatar:
            instance.avatar = avatar
            instance.save()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if request and instance.avatar:
            representation['avatar'] = request.build_absolute_uri(instance.avatar.url)
        return representation