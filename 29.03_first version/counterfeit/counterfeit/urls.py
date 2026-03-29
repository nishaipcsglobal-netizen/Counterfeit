from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from products import views as product_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # Public product verification UI
    path("", product_views.home, name="home"),
    path("verify/", product_views.home, name="verify"),
    path("scan-history/", product_views.scan_history, name="scan_history"),
    path("browse-products/", product_views.browse_products, name="browse_products"),

    # APIs / legacy routes
    path("verify-api/", product_views.verify_api, name="verify_api"),
    path("scan/", product_views.home, name="scan_legacy"),  # kept for backward compatibility

    # Manufacturer/admin workflows
    path("add-product/", product_views.add_product_to_blockchain, name="add_product"),
    path("register/", product_views.register, name="register"),
    path("login/", product_views.user_login, name="login"),
    path("admin-dashboard/", product_views.admin_dashboard, name="admin_dashboard"),
    path(
        "manufacturer-dashboard/",
        product_views.manufacturer_dashboard,
        name="manufacturer_dashboard",
    ),
    path("logout/", product_views.user_logout, name="logout"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)