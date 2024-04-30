# models.py
import os

from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

User = get_user_model()


def product_image_path(instance, filename):
    basename, extension = os.path.splitext(filename)
    new_filename = f"{instance.name}_{instance.id}{extension}"
    return os.path.join('product_images', new_filename)


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    quantity = models.IntegerField()
    product_type = models.CharField(max_length=100)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    manufacturer = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to=product_image_path, blank=True, null=True)

    def __str__(self):
        return f"Image for {self.product.name}"


class Basket(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class BasketProduct(models.Model):
    basket = models.ForeignKey(Basket, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()


@receiver(post_save, sender=User)
def create_basket(sender, instance, created, **kwargs):
    if created:
        Basket.objects.create(user=instance)

class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through='PurchaseItem')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateTimeField(auto_now_add=True)

    def formatted_date_time(self):
        return self.purchase_date.astimezone(timezone.get_default_timezone()).strftime('%Y-%m-%d %H:%M:%S')

class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()

class RefuelingHistory(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    car = models.ForeignKey('Car', on_delete=models.CASCADE)
    fuel_column = models.ForeignKey('FuelColumn', on_delete=models.CASCADE)
    fuel_type = models.ForeignKey('FuelType', on_delete=models.CASCADE)
    refueling_date_time = models.DateTimeField(auto_now_add=True)
    fuel_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    refueling_id = models.ForeignKey('FuelStation', on_delete=models.CASCADE)
    fuel_cost = models.DecimalField(max_digits=10, decimal_places=2)

    def formatted_date_time(self):
        return self.refueling_date_time.astimezone(timezone.get_default_timezone()).strftime('%Y-%m-%d %H:%M:%S')

    def __str__(self):
        return f"{self.refueling_date_time.strftime('%Y-%m-%d %H:%M:%S')}"


class CarBrand(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class CarModel(models.Model):
    brand = models.ForeignKey(CarBrand, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.brand.name} - {self.name}"


class Car(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    brand = models.ForeignKey(CarBrand, on_delete=models.CASCADE)
    model = models.ForeignKey(CarModel, on_delete=models.CASCADE)
    registration_number = models.CharField(max_length=20)
    fuel_tank_volume = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.brand} {self.model} ({self.registration_number}) для пользователя {self.user.username}"


# Заправки

class FuelType(models.Model):
    name = models.CharField(max_length=50)
    octane_number = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)

    def __str__(self):
        return self.name


class FuelColumn(models.Model):
    fuel_station = models.ForeignKey('FuelStation', related_name='columns', on_delete=models.CASCADE)
    number = models.IntegerField()
    fuel_type = models.ForeignKey(FuelType, on_delete=models.CASCADE)
    fuel_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_per_liter = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    def __str__(self):
        return f"FuelColumn {self.number} at {self.fuel_station.name} for {self.fuel_type.name}"


class FuelStation(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    fuel_type = models.ManyToManyField(FuelType, related_name='fuel_stations', through='FuelColumn')
    fuel_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.name
