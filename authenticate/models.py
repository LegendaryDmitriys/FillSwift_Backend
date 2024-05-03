import os

import jwt
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from datetime import datetime, timedelta
from django.db import models

from Gas import settings
from django.utils import timezone
import random
import string

from PIL import Image, ImageDraw, ImageFont


class UserManager(BaseUserManager):
    def create_user(self, username, lastname, firstname, email, password=None):
        if username is None:
            raise TypeError('Users must have a username.')

        if email is None:
            raise TypeError('Users must have an email address.')

        if lastname is None:
            raise TypeError('Users must have an lastname')

        if firstname is None:
            raise TypeError('Users must have an firstname')

        user = self.model(username=username, lastname=lastname, firstname=firstname,  email=self.normalize_email(email))
        user.set_password(password)
        user.save()

        return user

    def create_superuser(self, username, email, password):
        if password is None:
            raise TypeError('Superusers must have a password.')

        user = self.create_user(username, email, password)
        user.is_superuser = True
        user.is_staff = True
        user.save()

        return user

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(db_index=True, max_length=255, unique=True)
    firstname = models.CharField(db_index=True, max_length=255)
    lastname = models.CharField(db_index=True, max_length=255)
    email = models.EmailField(db_index=True, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    avatar = models.ImageField(upload_to='avatars', null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def token(self):
        return self._generate_jwt_token()

    def get_full_name(self):
        return "{} - {}".format(self.firstname, self.lastname)

    def _generate_jwt_token(self):
        dt = datetime.now() + timedelta(days=1)

        token = jwt.encode({
            'id': self.pk,
            'exp': int(dt.timestamp())
        }, settings.SECRET_KEY, algorithm='HS256')

        return token

    def save(self, *args, **kwargs):
        if not self.avatar:
            avatar_path = self._generate_avatar()
            self.avatar.name = avatar_path
        super().save(*args, **kwargs)

    def _generate_avatar(self):
        initials = self.firstname[0] + self.lastname[0]

        avatar_image = Image.new('RGB', (100, 100), color='grey')
        draw = ImageDraw.Draw(avatar_image)

        font = ImageFont.truetype(os.path.join(os.path.dirname(__file__), 'fonts', 'arial.ttf'), 40)

        text_size = draw.textbbox((0, 0), initials, font)
        text_width = text_size[2] - text_size[0]
        text_height = text_size[3] - text_size[1]

        x = (avatar_image.width - text_width) // 2
        y = (avatar_image.height - text_height) // 2

        draw.text((x, y), initials, fill='white', font=font)
        avatar_directory = os.path.join(settings.MEDIA_ROOT, 'avatars')
        avatar_path = os.path.join(avatar_directory, f'{self.username}_avatar.png')
        avatar_image.save(avatar_path)

        return avatar_path


class PasswordResetCode(models.Model):
    email = models.EmailField(unique=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)

    @staticmethod
    def generate_code():
        return ''.join(random.choices(string.ascii_letters + string.digits, k=6))