# file: app/urls.py

from django.urls import path
from .views import add_product_to_blockchain

urlpatterns = [
    path('add-product/', add_product_to_blockchain),
]