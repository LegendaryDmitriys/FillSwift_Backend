
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from backend.views import *
from rest_framework import routers
from django.conf import settings

router = routers.DefaultRouter()



refulings_patterns = [
    path('refuelings/', RefuelingHistoryListCreate.as_view(), name='refueling-history-list-create'),
    path('<int:user_id>/refuelings/', UserRefuelingHistoryList.as_view(), name='refueling-history-retrieve-update-destroy'),
    path('download/receipt/<int:refueling_id>/', download_receipt, name='download_receipt'),
    path('refueling_requests/', refueling_requests_list, name='refueling_requests_list'),
    path('change_refueling_request_status/<int:refueling_request_id>/', change_refueling_request_status, name='change_refueling_request_status'),
]

card_patterns = [
    path('baskets/', BasketListCreateAPIView.as_view(), name='basket-list-create'),
    path('baskets/<int:user_id>/', BasketRetrieveUpdateDestroyAPIView.as_view(), name='basket-detail'),
    path('basket-products/', BasketProductListCreateAPIView.as_view(), name='basketproduct-list-create'),
    path('basket-products/<int:basket_id>/', BasketProductListAPIView.as_view(), name='basketproduct-detail'),
    path('basket-products/<int:basket_id>/<int:pk>/', BasketProductRetrieveUpdateDestroyAPIView.as_view(),
         name='basket-product-detail'),
    path('purchases/', PurchaseListCreate.as_view(), name='purchase-list-create'),
    path('purchase/<int:user_id>/', PurchaseDetail.as_view(), name='purchase-detail'),
    path('purchases-list/', purchase_list, name='purchase-list'),
    path('purchase/<int:purchase_id>/change_status/', change_purchase_status, name='change_purchase_status'),
]

fuelstation_patterns = [
    path('list/', FuelStationListCreateAPIView.as_view(), name='fuelstation-list-create'),
    path('<int:pk>/', FuelStationDetailAPIView.as_view(), name='fuelstation-detail'),
    path('fuelcolumns/', FuelColumnListCreateAPIView.as_view(), name='fuelcolumn-list-create'),
    path('fuelcolumn/<int:fuel_station_id>', FuelColumnListByStationAPIView.as_view(), name='fuelcolumn-list-by-station'),
    path('<int:fuel_station_id>/fuelcolumn/<int:fuel_column_id>/',
         FuelColumnDetailByStationAPIView.as_view(), name='fuelcolumn-detail-by-station'),
    path('fueltypes/', FuelTypeListCreateAPIView.as_view(), name='fueltype-list'),
    path('fueltypes/<int:pk>/', FuelTypeDetailAPIView.as_view(), name='fueltype-detail'),
]

product_patterns = [
    path('products/', ProductListCreate.as_view(), name='product-list-create'),
    path('products/<int:pk>/', ProductRetrieveUpdateDestroy.as_view(), name='product-retrieve-update-destroy'),
    path('popular-products/', PopularProductsAPIView.as_view(), name='popular-products'),
    path('upload-image/', ProductImageUpload.as_view(), name='product_image_upload'),
]

cars_patterns = [
    path('list/', CarBrandWithModelsList.as_view(), name='car_brand_list_create'),
    path('brands/', CarBrandListCreate.as_view(), name='car_brand_list_create'),
    path('brand/<int:pk>/', CarBrandRetrieveUpdateDestroy.as_view(), name='car_brand_retrieve_update_destroy'),
    path('models/', CarModelListCreate.as_view(), name='car_model_list_create'),
    path('model/<int:pk>/', CarModelRetrieveUpdateDestroy.as_view(), name='car_model_retrieve_update_destroy'),
    path('users/', CarListCreate.as_view(), name='user_list_create'),
    path('user/<int:user_id>', UserCarsListView.as_view(), name='user_cars_detail'),
    path('user/<int:user_id>/<int:pk>/', CarUsersRetrieveUpdateDestroy.as_view(), name='car-detail'),
    path('cars/<int:id>/', CarRetrieveUpdateDestroy.as_view(), name='car-detail'),

]

stats_patterns = [
    path('avg-fuel-quantity/', AvgFuelQuantityStats.as_view(), name='avg-fuel-quantity'),
    path('car-brand-model-stats/', CarBrandModelStats.as_view(), name='car-brand-model-stats'),
    path('total-products-sold/', TotalProductsSoldStats.as_view(), name='total-products-sold'),
    path('avg-purchase-price/', AvgPurchasePriceStats.as_view(), name='avg-purchase-price'),
    path('total-fuel-refueled-stats/', TotalFuelRefueledStats.as_view(), name='total-fuel-refueled-stats'),
    path('total-spent-stats/',TotalSpentStats.as_view(), name='total-spent-stats')
]


urlpatterns = [
    path("auth/", include('rest_framework.urls')),
    path('api/', include('authenticate.urls', namespace='authentication')),
    path('carts/', include(card_patterns)),
    path('products/', include(product_patterns)),
    path('refuling/', include(refulings_patterns)),
    path('cars/', include(cars_patterns)),
    path('fuelstation/', include(fuelstation_patterns)),
    path('stats/', PurchaseAndRefuelingStats.as_view(), name='stats'),
    path('statistic/', include(stats_patterns)),
    path('user-history-count/<int:user_id>/', UserHistoryCountAPIView.as_view(), name='user_history_count'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

