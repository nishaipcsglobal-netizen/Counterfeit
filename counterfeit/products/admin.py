# FILE: products/admin.py
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Product, ScanLog

User = get_user_model()


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "role", "is_active", "is_staff", "is_superuser")
    list_filter = ("role", "is_active", "is_staff", "is_superuser")
    fieldsets = DjangoUserAdmin.fieldsets + (("Role", {"fields": ("role",)}),)
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (("Role", {"fields": ("role",)}),)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("product_id", "product_name", "category", "manufacturer_name", "manufacturer_user", "created_at")
    search_fields = ("product_id", "product_name", "category", "manufacturer_name")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "manufacturer_user":
            kwargs["queryset"] = User.objects.filter(role=User.ROLE_MANUFACTURER, is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(ScanLog)
class ScanLogAdmin(admin.ModelAdmin):
    list_display = ("product_id", "status", "scanned_at", "user", "client_ip")