import json
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db.models import Sum
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework import generics, viewsets, status
from rest_framework.generics import get_object_or_404, CreateAPIView
from rest_framework.views import APIView
from django.http import FileResponse, HttpResponse, JsonResponse
import os

from Gas import settings
from Gas.settings import MEDIA_ROOT, DEFAULT_FROM_EMAIL
from backend.models import Product, RefuelingHistory, CarBrand, CarModel, Car, Basket, BasketProduct, FuelStation, \
    Purchase, PurchaseItem, ProductImage, FuelColumn, FuelType
from backend.serializers import ProductSerializer, RefuelingHistorySerializer, \
    CarModelSerializer, CarBrandSerializer, CarSerializer, BasketSerializer, BasketProductSerializer, \
    FuelStationSerializer, CarBrandWithModelsSerializer, PurchaseSerializer, FuelColumnSerializer, FuelTypeSerializer

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Sum, F, Value, DateTimeField
from django.db.models.functions import TruncDay

from rest_framework import generics
from .models import Purchase, RefuelingHistory


User = get_user_model()


class ProductListCreate(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ProductRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class BasketListCreateAPIView(generics.ListCreateAPIView):
    queryset = Basket.objects.all()
    serializer_class = BasketSerializer

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        user_baskets = Basket.objects.filter(user_id=user_id)
        return user_baskets


class BasketRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Basket.objects.all()
    serializer_class = BasketSerializer
    lookup_field = 'user_id'

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        user_baskets = Basket.objects.filter(user_id=user_id)
        return user_baskets


class BasketProductListCreateAPIView(CreateAPIView):
    queryset = BasketProduct.objects.all()
    serializer_class = BasketProductSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        basket_id = data.get('basket')
        product_id = data.get('product')
        quantity = data.get('quantity')

        basket_product = BasketProduct.objects.filter(basket=basket_id, product=product_id).first()

        if basket_product:
            basket_product.quantity += int(quantity)
            basket_product.save()
            serializer = self.get_serializer(basket_product)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class BasketProductRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BasketProductSerializer
    lookup_field = 'basket_id'

    def get_queryset(self):
        basket_id = self.kwargs.get('basket_id')
        user_basket_products = BasketProduct.objects.filter(basket_id=basket_id)
        return user_basket_products

    def destroy(self, request, *args, **kwargs):
        try:
            basket_id = self.kwargs.get('basket_id')
            product_id = self.kwargs.get('pk')
            basket_products = BasketProduct.objects.filter(basket_id=basket_id, product_id=product_id)

            if basket_products.exists():
                if basket_products.count() == 1:
                    basket_products.delete()
                else:
                    basket_products.update(quantity=F('quantity') - 1)
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                raise ObjectDoesNotExist
        except ObjectDoesNotExist:
            return Response({"detail": "Товар не найден"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BasketProductListAPIView(generics.ListAPIView):
    serializer_class = BasketProductSerializer

    def get_queryset(self):
        basket_id = self.kwargs.get('basket_id')
        queryset = BasketProduct.objects.filter(basket_id=basket_id)
        return queryset


class PurchaseListCreate(APIView):
    def post(self, request):
        user_id = request.data.get('user')
        total_price = request.data.get('total_price')
        product_ids = request.data.get('productIds')
        quantities = request.data.get('quantities')

        try:
            purchase = Purchase.objects.create(
                user_id=user_id,
                total_price=total_price
            )

            user_basket = Basket.objects.get(user_id=user_id)

            for product_id, quantity in zip(product_ids, quantities):
                product = Product.objects.get(id=product_id)

                purchase_item = PurchaseItem.objects.create(
                    purchase=purchase,
                    product=product,
                    quantity=quantity
                )

                basket_product = BasketProduct.objects.get(basket=user_basket, product_id=product_id)
                basket_product.delete()

            create_purchase_pdf_and_send_receipt(sender=None, instance=purchase, created=True)

            return Response({'message': 'Покупка совершена'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



class PurchaseDetail(generics.ListAPIView):
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return Purchase.objects.filter(user_id=user_id, status='confirmed')

@receiver(post_save, sender=Purchase)
def create_purchase_pdf_and_send_receipt(sender, instance, created, **kwargs):
    if not created and instance.status == 'confirmed':
        pdf_buffer = generate_purchase_pdf(instance)

        file_path = f'{MEDIA_ROOT}/pdf_purchase/purchase_{instance.id}.pdf'

        with open(file_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())

        subject = 'Ваш чек с покупкой'
        message = 'Ваш чек с покупкой прикреплен к этому письму.'

        html_message = render_to_string('email/purchase_receipt_email.html', {'purchase': instance})
        plain_message = strip_tags(html_message)
        from_email = DEFAULT_FROM_EMAIL
        to_email = instance.user.email

        try:
            send_mail(subject, plain_message, from_email, [to_email], html_message=html_message, fail_silently=False)
        except Exception as e:
            print(f"Ошибка при отправке чека на почту: {e}")


def generate_purchase_pdf(purchase):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    pdfmetrics.registerFont(TTFont('Arial', '../fonts/Arial.ttf'))
    p.setFont("Arial", 12)

    html_content = render_to_string('email/purchase_receipt_email.html', {'purchase': purchase})

    p.setFont("Arial", 16)
    p.drawString(100, 780, "Информация о покупке")
    p.setFont("Arial", 12)
    p.drawString(100, 760, f"ID покупки: {purchase.id}")
    p.drawString(100, 740, f"Дата покупки: {purchase.purchase_date.strftime('%Y-%m-%d %H:%M:%S')}")

    p.line(100, 730, 500, 730)

    p.drawString(100, 710, "Детали покупки:")
    p.drawString(100, 690, "Продукт")
    p.drawString(250, 690, "Количество")
    p.drawString(400, 690, "Цена за единицу")
    p.drawString(500, 690, "Общая цена")

    row_height = 670
    for purchase_item in purchase.purchaseitem_set.all():
        product_name = purchase_item.product.name
        quantity = purchase_item.quantity
        price_per_unit = purchase_item.product.price_per_unit
        total_price = float(price_per_unit) * quantity

        if len(product_name) > 20:
            product_name = product_name[:20] + '...'

        p.drawString(100, row_height, product_name)
        p.drawString(250, row_height, str(quantity))
        p.drawString(400, row_height, str(price_per_unit))
        p.drawString(500, row_height, str(total_price))
        row_height -= 20

    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer



def download_purchase_receipt(request, purchase_id):
    try:
        file_path = f'{MEDIA_ROOT}/pdf_purchase/purchase_{purchase_id}.pdf'
        if os.path.exists(file_path):
            return FileResponse(open(file_path, 'rb'), as_attachment=True)
        else:
            return HttpResponse("Файл не найден", status=404)
    except Exception as e:
        return HttpResponse(f"Ошибка при скачивании файла: {str(e)}", status=500)



def purchase_list(request):
    purchases = Purchase.objects.all()
    data = []

    for purchase in purchases:
        purchase_data = {
            'id': purchase.id,
            'total_price': purchase.total_price,
            'purchase_date': purchase.formatted_date_time(),
            'status': purchase.status,
            'user': {
                'id': purchase.user.id,
                'username': purchase.user.username,
                'email': purchase.user.email,
                'firstname': purchase.user.firstname,
                'lastname': purchase.user.lastname,
            },
            'products': []
        }

        for purchase_item in purchase.purchaseitem_set.all():
            product_data = {
                'id': purchase_item.product.id,
                'name': purchase_item.product.name,
                'description': purchase_item.product.description,
                'quantity': purchase_item.quantity,
                'product_type': purchase_item.product.product_type,
                'price_per_unit': purchase_item.product.price_per_unit,
                'manufacturer': purchase_item.product.manufacturer
            }
            purchase_data['products'].append(product_data)

        data.append(purchase_data)

    return JsonResponse({'purchases': data})

@csrf_exempt
def change_purchase_status(request, purchase_id):
    try:
        purchase = Purchase.objects.get(id=purchase_id)
    except Purchase.DoesNotExist:
        return JsonResponse({'message': 'Покупка не найдена'}, status=404)

    if request.method == 'PATCH':
        try:
            request_data = json.loads(request.body)
            new_status = request_data.get('status')
        except json.JSONDecodeError:
            return JsonResponse({'message': 'Неверный формат данных'}, status=400)

        if new_status in dict(Purchase.STATUS_CHOICES):
            purchase.status = new_status
            purchase.save()
            return JsonResponse({'message': 'Статус успешно изменен', 'new_status': new_status})
        else:
            return JsonResponse({'message': 'Недопустимое значение статуса'}, status=400)

    return JsonResponse({'message': 'Метод не разрешен'}, status=405)


class RefuelingHistoryListCreate(generics.ListCreateAPIView):
    queryset = RefuelingHistory.objects.all()
    serializer_class = RefuelingHistorySerializer


class CarBrandListCreate(generics.ListCreateAPIView):
    queryset = CarBrand.objects.all()
    serializer_class = CarBrandSerializer


class CarBrandRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = CarBrand.objects.all()
    serializer_class = CarBrandSerializer


class CarModelListCreate(generics.ListCreateAPIView):
    queryset = CarModel.objects.all()
    serializer_class = CarModelSerializer


class CarModelRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = CarModel.objects.all()
    serializer_class = CarModelSerializer


class CarListCreate(generics.ListCreateAPIView):
    queryset = Car.objects.all()
    serializer_class = CarSerializer


class CarBrandWithModelsList(generics.ListCreateAPIView):
    queryset = CarBrand.objects.all()
    serializer_class = CarBrandWithModelsSerializer


class UserCarsListView(APIView):
    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        user_cars = Car.objects.filter(user=user)
        serializer = CarSerializer(user_cars, many=True)
        return Response(serializer.data)


class CarUsersRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CarSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return Car.objects.filter(user_id=user_id)



class CarRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CarSerializer
    lookup_field = 'id'

    def get_queryset(self):
        id = self.kwargs['id']
        return Car.objects.filter(id=id)


class UserRefuelingHistoryList(generics.ListAPIView):
    serializer_class = RefuelingHistorySerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return RefuelingHistory.objects.filter(user_id=user_id, status='confirmed')


@receiver(post_save, sender=RefuelingHistory)
def create_refueling_pdf_and_send_receipt(sender, instance, created, **kwargs):
    if not created and instance.status == 'confirmed':
        pdf_buffer = generate_refueling_pdf(instance)

        file_path = f'{MEDIA_ROOT}/pdf_refueling/refueling_{instance.id}.pdf'
        with open(file_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())

        subject = 'Ваш чек с заправкой'
        message = 'Ваш чек с заправкой прикреплен к этому письму.'

        html_message = render_to_string('email/receipt_email.html', {'refueling': instance})
        plain_message = strip_tags(html_message)
        from_email = DEFAULT_FROM_EMAIL
        to_email = instance.user.email

        try:
            send_mail(subject, plain_message, from_email, [to_email], html_message=html_message, fail_silently=False)
        except Exception as e:
            print(f"Ошибка при отправке чека на почту: {e}")

def generate_refueling_pdf(refueling):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    pdfmetrics.registerFont(TTFont('Arial', '../fonts/Arial.ttf'))
    p.setFont("Arial", 12)

    p.setFont("Arial", 16)
    p.drawString(100, 780, "ОАО FillSwift")
    p.setFont("Arial", 12)
    p.drawString(100, 760, f"АЗС - {refueling.fuel_column.fuel_station.id}")
    p.drawString(100, 740, f"{refueling.fuel_column.fuel_station.location}")

    p.line(100, 730, 500, 730)

    p.drawString(100, 710, f"ЧЕК {refueling.id}  {refueling.formatted_date_time()}")
    p.drawString(100, 690, f"{refueling.fuel_type.name}-{int(refueling.fuel_type.octane_number)}")
    p.drawString(100, 670, f"Количество топлива: {refueling.fuel_quantity} л")

    p.line(100, 660, 500, 660)

    p.drawString(100, 640, f"Стоимость топлива: {refueling.fuel_cost} руб")

    p.setFont("Arial", 16)
    p.drawString(100, 610, "ИТОГ:")
    p.setFont("Arial", 12)
    p.drawString(100, 590, f"РУБ {refueling.fuel_column.price_per_liter} * {refueling.fuel_quantity} Л")
    p.drawString(100, 570, f"ИТОГ       ={refueling.fuel_cost} ₽")

    p.line(100, 560, 500, 560)

    p.drawString(100, 540, "СПАСИБО ЗА ПОКУПКУ! ДОБРОГО ПУТИ!")

    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer


def download_receipt(request, refueling_id):
    try:
        file_path = f'{MEDIA_ROOT}/pdf_refueling/refueling_{refueling_id}.pdf'
        if os.path.exists(file_path):
            return FileResponse(open(file_path, 'rb'), as_attachment=True)
        else:
            return HttpResponse("Файл не найден", status=404)
    except Exception as e:
        return HttpResponse(f"Ошибка при скачивании файла: {str(e)}", status=500)


def refueling_requests_list(request):
    refueling_requests = RefuelingHistory.objects.select_related('user', 'car', 'fuel_column', 'fuel_type','h').values(
        'id',
        'user__id', 'user__username', 'user__email', 'user__lastname', 'user__firstname',
        'car__id', 'car__model__name', 'car__brand__name', 'car__registration_number',
        'fuel_column__id', 'fuel_column__number',
        'fuel_type__id', 'fuel_type__name', 'fuel_column__fuel_type__octane_number',
        'fuel_quantity',
        'refueling_id',
        'fuel_cost',
        'refueling_date_time',
        'status'
    )
    return JsonResponse({'refueling_requests': list(refueling_requests)})

@csrf_exempt
def change_refueling_request_status(request, refueling_request_id):
    try:
        refueling_request = RefuelingHistory.objects.get(id=refueling_request_id)
    except RefuelingHistory.DoesNotExist:
        return JsonResponse({'message': 'Запрос на заправку не найден'}, status=404)

    if request.method == 'PATCH':
        try:
            request_data = json.loads(request.body)
            new_status = request_data.get('status')
        except json.JSONDecodeError:
            return JsonResponse({'message': 'Неверный формат данных'}, status=400)



        if new_status in dict(RefuelingHistory.STATUS_CHOICES):
            refueling_request.status = new_status
            refueling_request.save()
            return JsonResponse({'message': 'Статус успешно изменен', 'new_status': new_status})
        else:
            return JsonResponse({'message': 'Недопустимое значение статуса'}, status=400)

    return JsonResponse({'message': 'Метод не разрешен'}, status=405)

class FuelStationListCreateAPIView(generics.ListCreateAPIView):
    queryset = FuelStation.objects.all()
    serializer_class = FuelStationSerializer


class FuelStationDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FuelStation.objects.all()
    serializer_class = FuelStationSerializer


class PopularProductsAPIView(APIView):
    def get(self, request):
        popular_products = PurchaseItem.objects.values('product').annotate(total_sales=Count('product')).order_by(
            '-total_sales')[:10]
        product_ids = [item['product'] for item in popular_products]
        products = Product.objects.filter(id__in=product_ids)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

class PurchaseAndRefuelingStats(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        month = request.GET.get('month')
        year = request.GET.get('year')

        if month is None or year is None:
            return JsonResponse({'error': 'Month and year parameters are required'}, status=400)

        month = int(month)
        year = int(year)

        purchase_stats = Purchase.objects.filter(purchase_date__month=month, purchase_date__year=year) \
            .annotate(day=TruncDay('purchase_date', output_field=DateTimeField())) \
            .values('day') \
            .annotate(count=Count('id')) \
            .order_by('day')

        refueling_stats = RefuelingHistory.objects.filter(refueling_date_time__month=month,
                                                          refueling_date_time__year=year) \
            .annotate(day=TruncDay('refueling_date_time')) \
            .values('day') \
            .annotate(count=Count('id'), total_cost=Sum('fuel_cost'), category=Value('refueling'),
                      status=Value('refueling')) \
            .order_by('day')

        return JsonResponse({'purchases': list(purchase_stats), 'refuelings': list(refueling_stats)})


class FuelColumnListCreateAPIView(generics.ListCreateAPIView):
    queryset = FuelColumn.objects.all()
    serializer_class = FuelColumnSerializer

class FuelColumnListByStationAPIView(generics.ListCreateAPIView):
    serializer_class = FuelColumnSerializer

    def get_queryset(self):
        fuel_station_id = self.kwargs.get('fuel_station_id')
        return FuelColumn.objects.filter(fuel_station_id=fuel_station_id)

    def perform_create(self, serializer):
        fuel_station_id = self.kwargs.get('fuel_station_id')
        serializer.save(fuel_station_id=fuel_station_id)


class FuelColumnDetailByStationAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FuelColumn.objects.all()
    serializer_class = FuelColumnSerializer
    lookup_url_kwarg = 'fuel_column_id'

    def get_queryset(self):
        fuel_station_id = self.kwargs.get('fuel_station_id')
        return FuelColumn.objects.filter(fuel_station_id=fuel_station_id)

class FuelTypeListCreateAPIView(generics.ListCreateAPIView):
    queryset = FuelType.objects.all()
    serializer_class = FuelTypeSerializer

class FuelTypeDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FuelType.objects.all()
    serializer_class = FuelTypeSerializer


class UserHistoryCountAPIView(APIView):
    def get(self, request, user_id, format=None):
        refueling_count = RefuelingHistory.objects.filter(user_id=user_id).count()
        purchase_count = Purchase.objects.filter(user_id=user_id).count()
        return Response({
            'refueling_count': refueling_count,
            'purchase_count': purchase_count
        }, status=status.HTTP_200_OK)


# графики

from django.db.models import Avg
class AvgFuelQuantityStats(APIView):
    def get(self, request):
        avg_fuel_quantity = RefuelingHistory.objects.aggregate(avg_fuel_quantity=Avg('fuel_quantity'))
        return Response(avg_fuel_quantity)

class CarBrandModelStats(APIView):
    def get(self, request):
        car_brand_model_stats = Car.objects.values('brand__name', 'model__name').annotate(count=Count('id'))
        return Response(car_brand_model_stats)



class TotalProductsSoldStats(APIView):
    def get(self, request):
        total_products_sold = PurchaseItem.objects.filter(purchase__purchase_date__month=5, purchase__purchase_date__year=2024).aggregate(total_products_sold=Sum('quantity'))
        return Response(total_products_sold)


class AvgPurchasePriceStats(APIView):
    def get(self, request):
        avg_purchase_price = Purchase.objects.aggregate(avg_purchase_price=Avg('total_price'))
        return Response(avg_purchase_price)