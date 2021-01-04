from django.contrib import admin
from django.urls import path, include
from shop.views import StoreListView, ProductView, CheckoutView, CartView, update_item


urlpatterns = [
    path('', StoreListView.as_view(), name='store'),
    path('product/<slug>', ProductView.as_view(), name='product'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('cart/', CartView.as_view(), name='cart'),
    path('update_item/', update_item, name='update-item'),

]
