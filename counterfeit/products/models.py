from __future__ import annotations

import hashlib
from io import BytesIO

import qrcode
from django.contrib.auth.models import AbstractUser
from django.core.files import File
from django.db import models


class User(AbstractUser):
    ROLE_ADMIN = "admin"
    ROLE_MANUFACTURER = "manufacturer"
    ROLE_CUSTOMER = "customer"

    ROLE_CHOICES = (
        (ROLE_ADMIN, "Admin"),
        (ROLE_MANUFACTURER, "Manufacturer"),
        (ROLE_CUSTOMER, "Customer"),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CUSTOMER)

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"


class Product(models.Model):
    product_id = models.CharField(max_length=100, unique=True)
    product_name = models.CharField(max_length=200)
    category = models.CharField(max_length=120)
    manufacturer_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="products",
        limit_choices_to={"role": User.ROLE_MANUFACTURER},
    )
    manufacturer_name = models.CharField(max_length=200)
    hash_value = models.CharField(max_length=64, blank=True)
    qr_code = models.ImageField(upload_to="qrcodes/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def compute_hash(self) -> str:
        # SHA-256 algorithm required by spec
        data = f"{self.product_id}|{self.product_name}|{self.category}|{self.manufacturer_name}"
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def save(self, *args, **kwargs):
        if not self.manufacturer_name:
            self.manufacturer_name = self.manufacturer_user.username

        self.hash_value = self.compute_hash()

        qr_payload = f"{self.product_id}|{self.hash_value}"
        qr_img = qrcode.make(qr_payload)

        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        file_name = f"{self.product_id}.png"
        self.qr_code.save(file_name, File(buffer), save=False)

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.product_name} ({self.product_id})"

# FILE: products/models.py  (ADD below ScanLog)
class BrowseLog(models.Model):
    browsed_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    client_ip = models.GenericIPAddressField(null=True, blank=True)

    # snapshot for reporting
    role = models.CharField(max_length=20, blank=True)
    products_shown = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("-browsed_at",)

    def save(self, *args, **kwargs):
        if not self.role and self.user:
            self.role = getattr(self.user, "role", "")
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return(
            f"{self.user.username} browsed ({self.products_shown}) "
            f"@ {self.browsed_at:%Y-%m-%d %H:%M}"
         )

class ScanLog(models.Model):
    STATUS_AUTHENTIC = "AUTHENTIC"
    STATUS_FAKE = "FAKE"
    STATUS_ERROR = "ERROR"

    STATUS_CHOICES = (
        (STATUS_AUTHENTIC, "Authentic"),
        (STATUS_FAKE, "Fake"),
        (STATUS_ERROR, "Error"),
    )

    product_id = models.CharField(max_length=150)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    scanned_at = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    client_ip = models.GenericIPAddressField(null=True, blank=True)

    # snapshot (so scan history keeps details even if product changes)
    product_name = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=120, blank=True)
    manufacturer_name = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ("-scanned_at",)

    def __str__(self) -> str:
        return f"{self.product_id} - {self.status}"
