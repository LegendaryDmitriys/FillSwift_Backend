
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from backend.views import *
from rest_framework import routers
from django.conf import settings

router = routers.DefaultRouter()
from django.contrib.auth import views as auth_views


refulings_patterns = [
    path('refuelings/', RefuelingHistoryListCreate.as_view(), name='refueling-history-list-create'),
    path('<int:user_id>/refuelings/', UserRefuelingHistoryList.as_view(), name='refueling-history-retrieve-update-destroy'),
    path('download/receipt/<int:refueling_id>/', download_receipt, name='download_receipt'),
]

card_patterns = [
    path('baskets/', BasketListCreateAPIView.as_view(), name='basket-list-create'),
    path('baskets/<int:user_id>/', BasketRetrieveUpdateDestroyAPIView.as_view(), name='basket-detail'),
    path('basket-products/', BasketProductListCreateAPIView.as_view(), name='basketproduct-list-create'),
    path('basket-products/<int:basket_id>/', BasketProductListAPIView.as_view(), name='basketproduct-detail'),
    path('basket-products/<int:basket_id>/<int:pk>/', BasketProductRetrieveUpdateDestroyAPIView.as_view(),
         name='basket-product-detail'),
    path('purchases/', PurchaseListCreate.as_view(), name='purchase-list'),
    path('purchase/<int:user_id>/', PurchaseDetail.as_view(), name='purchase-detail'),
]

fuelstation_patterns = [
    path('list/', FuelStationListCreateAPIView.as_view(), name='fuelstation-list-create'),
    path('<int:pk>/', FuelStationDetailAPIView.as_view(), name='fuelstation-detail')
]

product_patterns = [
    path('products/', ProductListCreate.as_view(), name='product-list-create'),
    path('products/<int:pk>/', ProductRetrieveUpdateDestroy.as_view(), name='product-retrieve-update-destroy'),
    path('popular-products/', PopularProductsAPIView.as_view(), name='popular-products'),
]

cars_patterns = [
    path('list/', CarBrandWithModelsList.as_view(), name='car_brand_list_create'),
    path('brands/', CarBrandListCreate.as_view(), name='car_brand_list_create'),
    path('brand/<int:pk>/', CarBrandRetrieveUpdateDestroy.as_view(), name='car_brand_retrieve_update_destroy'),
    path('models/', CarModelListCreate.as_view(), name='car_model_list_create'),
    path('model/<int:pk>/', CarModelRetrieveUpdateDestroy.as_view(), name='car_model_retrieve_update_destroy'),
    path('users/', CarListCreate.as_view(), name='user_list_create'),
    path('user/<int:user_id>', UserCarsListView.as_view(), name='user_cars_detail'),
    path('user/<int:user_id>/<int:pk>/', CarRetrieveUpdateDestroy.as_view(), name='car-detail'),
]



urlpatterns = [
    path("auth/", include('rest_framework.urls')),
    path('api/', include('authenticate.urls', namespace='authentication')),
    path('carts/', include(card_patterns)),
    path('products/', include(product_patterns)),
    path('refuling/', include(refulings_patterns)),
    path('cars/', include(cars_patterns)),
    path('fuelstation/', include(fuelstation_patterns))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

