from django.contrib import admin

from .models import Product, ScanLog


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("product_id", "product_name", "manufacturer", "created_at")
    search_fields = ("product_id", "product_name", "manufacturer")
    list_filter = ("manufacturer",)


@admin.register(ScanLog)
class ScanLogAdmin(admin.ModelAdmin):
    list_display = ("product_id", "product_name", "status", "scanned_at", "user", "client_ip")
    search_fields = ("product_id", "product_name", "status", "client_ip")
    list_filter = ("status", "scanned_at")
