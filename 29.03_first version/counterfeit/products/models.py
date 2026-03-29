from __future__ import annotations

import hashlib
from io import BytesIO

import qrcode
from django.contrib.auth.models import AbstractUser
from django.core.files import File
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("manufacturer", "Manufacturer"),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)


class Product(models.Model):
    product_id = models.CharField(max_length=100, unique=True)
    product_name = models.CharField(max_length=200)
    manufacturer = models.CharField(max_length=200)
    hash_value = models.CharField(max_length=64, blank=True)
    qr_code = models.ImageField(upload_to="qrcodes/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        data = f"{self.product_id}{self.product_name}{self.manufacturer}"
        self.hash_value = hashlib.sha256(data.encode()).hexdigest()

        qr_data = f"{self.product_id}|{self.hash_value}"
        qr_img = qrcode.make(qr_data)

        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        file_name = f"{self.product_id}.png"
        self.qr_code.save(file_name, File(buffer), save=False)

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.product_name} ({self.product_id})"


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
    product_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    scanned_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    client_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ("-scanned_at",)

    def __str__(self) -> str:
        return f"{self.product_id} - {self.status} @ {self.scanned_at:%Y-%m-%d %H:%M}"