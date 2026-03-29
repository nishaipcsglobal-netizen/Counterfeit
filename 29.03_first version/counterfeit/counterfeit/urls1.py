"""
URL configuration for counterfeit project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from products.views import verify_product
from products.views import add_product_to_blockchain
from products.views import verify_api
from django.shortcuts import render
from products.views import register, user_login, admin_dashboard, manufacturer_dashboard
from products.views import user_logout

urlpatterns = [
    path('admin/', admin.site.urls),
    path('verify/', verify_product, name='verify'),
    path('add-product/', add_product_to_blockchain),
    path('scan/', lambda request: render(request, "scan.html")),
    path('verify-api/', verify_api),
    path('register/', register),
    path('login/', user_login),
    path('admin-dashboard/', admin_dashboard),
    path('manufacturer-dashboard/', manufacturer_dashboard),
    path('logout/', user_logout),
]
if settings.DEBUG:
   urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)