from django.db import models
import hashlib
import qrcode
from io import BytesIO
from django.core.files import File

from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('manufacturer', 'Manufacturer'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)


class Product(models.Model):
    product_id = models.CharField(max_length=100, unique=True)
    product_name = models.CharField(max_length=200)
    manufacturer = models.CharField(max_length=200)
    hash_value = models.CharField(max_length=64, blank=True)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True)
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

    def _str_(self):
        return f"{self.product_name} ({self.product_id})"