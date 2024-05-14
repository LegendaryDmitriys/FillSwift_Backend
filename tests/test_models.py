import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from rest_framework import status
from django.test import TestCase

from authenticate.models import PasswordResetCode, User
from backend.models import Product, Purchase, BasketProduct, Basket, Car, CarModel, CarBrand
from backend.serializers import CarSerializer


class UserModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            lastname='Doe',
            firstname='John',
            email='test@example.com',
            password='testpassword'
        )

    def test_user_creation(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpassword'))

    def test_user_full_name(self):
        self.assertEqual(self.user.get_full_name(), 'John - Doe')

    def test_user_token_generation(self):
        token = self.user.token
        self.assertTrue(token)

    def test_user_avatar_generation(self):
        self.user.save()
        self.assertTrue(self.user.avatar)

    def test_user_total_spent_update(self):
        self.user.update_total_spent(100)
        self.assertEqual(self.user.total_spent, 100)

    def test_user_total_refueled_update(self):
        self.user.update_total_refueled(10, 50)
        self.assertEqual(self.user.total_refueled, 10)
        self.assertEqual(self.user.total_spent, 50)

class PasswordResetCodeModelTestCase(TestCase):
    def setUp(self):
        self.reset_code = PasswordResetCode.objects.create(
            email='test@example.com',
            code='abcdef'
        )

    def test_reset_code_creation(self):
        self.assertEqual(self.reset_code.email, 'test@example.com')
        self.assertEqual(self.reset_code.code, 'abcdef')
        self.assertTrue(self.reset_code.created_at)

    def test_code_generation(self):
        code = PasswordResetCode.generate_code()
        self.assertEqual(len(code), 6)



class ProductModelTestCase(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            quantity=10,
            product_type='Test Type',
            price_per_unit=Decimal('10.00'),
            manufacturer='Test Manufacturer'
        )

    def test_product_creation(self):
        self.assertEqual(self.product.name, 'Test Product')
        self.assertEqual(self.product.quantity, 10)
        self.assertEqual(self.product.description, 'Test Description')
        self.assertEqual(self.product.product_type, 'Test Type')
        self.assertEqual(self.product.manufacturer, 'Test Manufacturer')


class ProductModelUpdateTestCase(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            quantity=10,
            product_type='Test Type',
            price_per_unit=Decimal('10.00'),
            manufacturer='Test Manufacturer'
        )

    def test_update_product_name(self):
        new_name = 'Updated Product Name'
        self.product.name = new_name
        self.product.save()
        updated_product = Product.objects.get(id=self.product.id)
        self.assertEqual(updated_product.name, new_name)

    def test_update_product_quantity(self):
        new_quantity = 20
        self.product.quantity = new_quantity
        self.product.save()
        updated_product = Product.objects.get(id=self.product.id)
        self.assertEqual(updated_product.quantity, new_quantity)



class ProductModelDeleteTestCase(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            quantity=10,
            product_type='Test Type',
            price_per_unit=Decimal('10.00'),
            manufacturer='Test Manufacturer'
        )

    def test_delete_product(self):
        product_id = self.product.id
        self.product.delete()
        with self.assertRaises(Product.DoesNotExist):
            Product.objects.get(id=product_id)


class TestTotalProductsSoldStats(APITestCase):
    def test_total_products_sold_stats(self):
        url = reverse('total-products-sold')
        response = self.client.get(url, {'month': 5, 'year': 2024})
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_products_sold', response.data)


class CarSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password', lastname='test', firstname='test')
        self.brand = CarBrand.objects.create(name='Toyota')
        self.model = CarModel.objects.create(name='Corolla', brand=self.brand)
        self.car_data = {
            'registration_number': 'A123BC',
            'fuel_tank_volume': 60,
            'user': self.user,
            'brand': self.brand,
            'model': self.model,
        }

    def test_unique_registration_number(self):
        Car.objects.create(**self.car_data)
        serializer = CarSerializer(data=self.car_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('user', serializer.errors)
        self.assertEqual(serializer.errors['user'][0].code, 'incorrect_type')

    def test_invalid_registration_number_format(self):
        self.car_data['registration_number'] = '123ABC'
        serializer = CarSerializer(data=self.car_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('registration_number', serializer.errors)
        self.assertEqual(serializer.errors['registration_number'][0], "Неправильный формат регистрационного номера. Номер должен быть в формате - A999AA.")