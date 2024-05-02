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
    Purchase, PurchaseItem
from backend.serializers import ProductSerializer, RefuelingHistorySerializer, \
    CarModelSerializer, CarBrandSerializer, CarSerializer, BasketSerializer, BasketProductSerializer, \
    FuelStationSerializer, CarBrandWithModelsSerializer, PurchaseSerializer

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from django.views.decorators.csrf import csrf_exempt

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
        return Purchase.objects.filter(user_id=user_id)


@receiver(post_save, sender=Purchase)
def create_purchase_pdf_and_send_receipt(sender, instance, created, **kwargs):
    if created:
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
        return RefuelingHistory.objects.filter(user_id=user_id)


@receiver(post_save, sender=RefuelingHistory)
def create_refueling_pdf_and_send_receipt(sender, instance, created, **kwargs):
    if created:

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


# Заправки

class FuelStationListCreateAPIView(generics.ListCreateAPIView):
    queryset = FuelStation.objects.all()
    serializer_class = FuelStationSerializer


class FuelStationDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FuelStation.objects.all()
    serializer_class = FuelStationSerializer


class PopularProductsAPIView(APIView):
    def get(self, request):
        popular_products = BasketProduct.objects.values('product').annotate(total_sales=Sum('quantity')).order_by(
            '-total_sales')[:10]
        product_ids = [item['product'] for item in popular_products]
        products = Product.objects.filter(id__in=product_ids)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

# class UserCarsView(models.Model):
#     user_username = models.CharField(max_length=150)
#     car_brand = models.CharField(max_length=100)
#     car_model = models.CharField(max_length=100)
#     registration_number = models.CharField(max_length=20)
#
#     class Meta:
#         managed = False
#         db_table = 'user_cars_view'
#
#
# user_cars = UserCarsView.objects.all()
# for car in user_cars:
#     print(car.user_username, car.car_brand, car.car_model, car.registration_number)

# class FuelStationInfoView(models.Model):
#     station_name = models.CharField(max_length=100)
#     station_location = models.CharField(max_length=255)
#     column_number = models.IntegerField()
#     fuel_type = models.CharField(max_length=50)
#     column_fuel_quantity = models.DecimalField(max_digits=10, decimal_places=2)
#     price_per_liter = models.DecimalField(max_digits=6, decimal_places=2)
#
#     class Meta:
#         managed = False
#         db_table = 'fuel_station_info_view'

# class Migration_Remove_Product_From_Basket(migrations.Migration):
#     operations = [
#         migrations.RunSQL('''
#             CREATE OR REPLACE FUNCTION remove_product_from_basket(
#                 IN user_id INT,
#                 IN product_id INT
#             )
#             RETURNS VOID
#             AS $$
#             BEGIN
#                 DELETE FROM backend_basketproduct
#                 WHERE basket_id = (SELECT id FROM backend_basket WHERE user_id = user_id)
#                 AND product_id = product_id;
#             END;
#             $$ LANGUAGE plpgsql;
#         ''')
#     ]



