from __future__ import annotations

import json
from typing import Any, Optional

import requests
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from .models import Product, ScanLog, User


def home(request: HttpRequest):
    return render(request, "home.html", {"active_tab": "verify"})


def scan_history(request: HttpRequest):
    logs = ScanLog.objects.all()[:200]
    return render(request, "scan_history.html", {"active_tab": "scan_history", "logs": logs})


def browse_products(request: HttpRequest):
    products = Product.objects.all().order_by("-created_at")[:500]
    return render(request, "browse_products.html", {"active_tab": "browse_products", "products": products})


def _get_client_ip(request: HttpRequest) -> Optional[str]:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


@csrf_exempt
def verify_api(request: HttpRequest):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"status": ScanLog.STATUS_ERROR, "error": "Invalid JSON"}, status=400)

    raw_product_id = (payload.get("product_id") or "").strip()
    if not raw_product_id:
        return JsonResponse({"status": ScanLog.STATUS_ERROR, "error": "product_id is required"}, status=400)

    product_id = raw_product_id.split("|", 1)[0].strip()

    status = ScanLog.STATUS_FAKE
    name: str = ""

    try:
        res = requests.get("http://localhost:3000/blockchain", timeout=5)
        res.raise_for_status()
        chain = res.json().get("chain", [])

        for block in chain:
            for item in block.get("data", []):
                if str(item.get("product_id", "")).strip() == product_id:
                    status = ScanLog.STATUS_AUTHENTIC
                    name = str(item.get("name", "") or "")
                    break
            if status == ScanLog.STATUS_AUTHENTIC:
                break

        ScanLog.objects.create(
            product_id=product_id,
            product_name=name,
            status=status,
            user=request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
            client_ip=_get_client_ip(request),
        )

        return JsonResponse({"status": status, "product_id": product_id, "name": name})

    except Exception as e:
        ScanLog.objects.create(
            product_id=product_id,
            product_name=name,
            status=ScanLog.STATUS_ERROR,
            user=request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
            client_ip=_get_client_ip(request),
        )
        return JsonResponse({"status": ScanLog.STATUS_ERROR, "error": str(e)}, status=500)


def user_logout(request: HttpRequest):
    logout(request)
    return redirect("/login/")


def register(request: HttpRequest):
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        role = request.POST.get("role") or "manufacturer"

        if not username or not password:
            return render(request, "register.html", {"error": "Username and password are required."})

        User.objects.create_user(username=username, password=password, role=role)
        return redirect("/login/")

    return render(request, "register.html")


def user_login(request: HttpRequest):
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("/admin-dashboard/" if user.role == "admin" else "/manufacturer-dashboard/")

        return render(request, "login.html", {"error": "Invalid credentials."})

    return render(request, "login.html")


@login_required
def admin_dashboard(request: HttpRequest):
    return render(request, "admin_dashboard.html")


@login_required
def manufacturer_dashboard(request: HttpRequest):
    return render(request, "manufacturer_dashboard.html")


def add_product_to_blockchain(request: HttpRequest):
    if request.method == "GET":
        return render(request, "add_product.html")

    product_id = (request.POST.get("product_id") or "").strip()
    name = (request.POST.get("name") or "").strip()

    if not product_id or not name:
        return render(request, "add_product.html", {"error": "Product ID and Name are required."})

    data: dict[str, Any] = {"product_id": product_id, "name": name}

    try:
        requests.post("http://localhost:3000/product", json=data, timeout=5).raise_for_status()
        requests.get("http://localhost:3000/mine", timeout=5).raise_for_status()

        from pathlib import Path

        qr_folder = Path(settings.MEDIA_ROOT) / "qrcodes"
        qr_folder.mkdir(parents=True, exist_ok=True)

        qr_filename = f"{product_id}.png"
        qr_path = qr_folder / qr_filename

        import qrcode

        img = qrcode.make(product_id)
        img.save(qr_path)

        qr_url = f"{settings.MEDIA_URL}qrcodes/{qr_filename}"
        return render(request, "result.html", {"product_id": product_id, "qr_url": qr_url})

    except Exception as e:
        return render(request, "add_product.html", {"error": str(e)})
