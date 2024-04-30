from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import re

from backend.models import Product, RefuelingHistory, CarModel, CarBrand, Car, Basket, BasketProduct, FuelStation, \
    FuelType, FuelColumn, ProductImage, Purchase, PurchaseItem


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('image',)

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = '__all__'

class PurchaseItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = PurchaseItem
        fields = '__all__'

class PurchaseSerializer(serializers.ModelSerializer):
    products = PurchaseItemSerializer(many=True, source='purchaseitem_set')

    class Meta:
        model = Purchase
        fields = ['id', 'total_price', 'purchase_date', 'user', 'products']

class BasketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Basket
        fields = ['id', 'user']

class BasketProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasketProduct
        fields = ['id', 'basket', 'product','quantity']


class RefuelingHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RefuelingHistory
        fields = '__all__'


# Авто

class CarModelSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source='brand.name', read_only=True)

    class Meta:
        model = CarModel
        fields = ['id', 'name', 'brand_name', 'brand_id']

class CarBrandSerializer(serializers.ModelSerializer):
    models = CarModelSerializer(many=True, read_only=True)
    class Meta:
        model = CarBrand
        fields = '__all__'





class CarSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    model_name = serializers.CharField(source='model.name', read_only=True)

    def validate_registration_number(self, value):
        if Car.objects.filter(registration_number=value).exists():
            raise serializers.ValidationError("Этот номер автомобиля уже зарегистрирован.")
        return value

    def validate_registration_number(self, value):
        if not re.match(r'^[A-Za-z]\d{3}[A-Za-z]{2}$', value):
            raise serializers.ValidationError(
                "Неправильный формат регистрационного номера. Номер должен быть в формате - A999AA.")
        return value

    class Meta:
        model = Car
        fields = ['id', 'registration_number', 'fuel_tank_volume', 'user', 'brand', 'brand_name', 'model', 'model_name']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['brand_name'] = instance.brand.name
        data['model_name'] = instance.model.name
        return data
class CarBrandWithModelsSerializer(serializers.ModelSerializer):
    models = CarModelSerializer(many=True, read_only=True)
    models_name = serializers.CharField(source='models.name', read_only=True)

    class Meta:
        model = CarBrand
        fields = ['id', 'name', 'models','models_name']

# Заправки

class FuelTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuelType
        fields = '__all__'


class FuelColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuelColumn
        fields = '__all__'




class FuelStationSerializer(serializers.ModelSerializer):
    fuel_columns = FuelColumnSerializer(many=True, read_only=True)
    fuel_types = serializers.SerializerMethodField()

    class Meta:
        model = FuelStation
        fields = '__all__'

    def get_fuel_types(self, obj):
        fuel_types = obj.fuel_type.all()
        return FuelTypeSerializer(fuel_types, many=True).data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        fuel_columns = FuelColumnSerializer(instance.columns.all(), many=True).data
        data['fuel_columns'] = fuel_columns
        return data