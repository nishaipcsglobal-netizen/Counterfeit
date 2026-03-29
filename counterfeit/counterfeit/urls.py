# FILE: counterfeit/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from products import views as product_views

urlpatterns = [
    # ✅ Custom App Admin pages MUST come before Django admin
    path("admin/manage-users/", product_views.manage_users, name="manage_users"),
    path("admin/add-user/", product_views.add_user, name="add_user"),
    path("admin/toggle-user/<int:user_id>/", product_views.toggle_user_active, name="toggle_user_active"),

    # Django admin
    path("admin/", admin.site.urls),

    # Customer
    path("", product_views.home, name="home"),
    path("verify/", product_views.home, name="verify"),
    path("scan-history/", product_views.scan_history, name="scan_history"),
    path("browse-products/", product_views.browse_products, name="browse_products"),
    path("browse-history/", product_views.browse_history, name="browse_history"),
    # APIs
    path("verify-api/", product_views.verify_api, name="verify_api"),

    # Auth
    path("register/", product_views.register, name="register"),
    path("login/", product_views.user_login, name="login"),
    path("logout/", product_views.user_logout, name="logout"),

    # Dashboards
    path("admin-dashboard/", product_views.admin_dashboard, name="admin_dashboard"),
    path("manufacturer-dashboard/", product_views.manufacturer_dashboard, name="manufacturer_dashboard"),

    # Manufacturer module
    path("manufacturer/register-product/", product_views.register_product, name="register_product"),
    path("manufacturer/my-products/", product_views.my_products, name="my_products"),
    path("manufacturer/generated-qrs/", product_views.generated_qrs, name="generated_qrs"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)