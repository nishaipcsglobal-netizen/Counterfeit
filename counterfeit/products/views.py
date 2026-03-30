# FILE: products/views.py
from __future__ import annotations

import json
from typing import Any, Optional

import requests
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from .decorators import role_required
from .forms import AdminCreateUserForm
from .models import Product, ScanLog

from django.http import HttpResponse
import qrcode
from io import BytesIO

User = get_user_model()


# -----------------------------
# Helpers
# -----------------------------
def _get_client_ip(request: HttpRequest) -> Optional[str]:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _parse_qr_value(raw: str) -> tuple[str, str]:
    """
    QR payload format: product_id|hash_value
    Returns (product_id, hash_value_or_empty).
    """
    raw = (raw or "").strip()
    if not raw:
        return "", ""
    if "|" not in raw:
        return raw, ""
    pid, h = raw.split("|", 1)
    return pid.strip(), h.strip()


# -----------------------------
# Customer module
# -----------------------------
@login_required
def home(request: HttpRequest):
    return render(request, "home.html", {"active_tab": "verify"})

@login_required
def scan_history(request: HttpRequest):
    user = request.user
    if getattr(user, "role", None) == User.ROLE_ADMIN:
        logs = ScanLog.objects.all()[:200]
    else:
        logs = ScanLog.objects.filter(user=user)[:200]

    return render(
        request,
        "scan_history.html",
        {
            "active_tab": "scan_history",
            "logs": logs,
        },
    )

@login_required
def browse_history(request: HttpRequest):
    u = request.user

    qs = BrowseLog.objects.select_related("user")
    if getattr(u, "role", None) == User.ROLE_ADMIN:
        logs = qs.all()[:300]
    else:
        logs = qs.filter(user_id=u.id)[:300]  # ✅ strict per-user filter

    return render(
        request,
        "browse_history.html",
        {
            "active_tab": "browse_history",
            "logs": logs,
        },
    )

@login_required
def browse_products(request: HttpRequest):
    user = request.user
    role = getattr(user, "role", None)

    if role == User.ROLE_ADMIN:
        products = Product.objects.all().order_by("-created_at")[:500]
    elif role == User.ROLE_MANUFACTURER:
        products = Product.objects.filter(manufacturer_user=user).order_by("-created_at")[:500]
    else:
        products = Product.objects.all().order_by("-created_at")[:500]

    return render(
        request,
        "browse_products.html",
        {
            "active_tab": "browse_products",
            "products": products,
        },
    )


@csrf_exempt
@login_required
def verify_api(request: HttpRequest):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"status": ScanLog.STATUS_ERROR, "error": "Invalid JSON"}, status=400)

    raw_value = (payload.get("product_id") or "").strip()
    pid, qr_hash = _parse_qr_value(raw_value)
    if not pid:
        return JsonResponse({"status": ScanLog.STATUS_ERROR, "error": "product_id is required"}, status=400)

    product: Optional[Product] = Product.objects.filter(product_id=pid).first()
    db_hash_ok = False

    if product:
        db_hash_ok = (not qr_hash) or (qr_hash == product.hash_value)

    # optional blockchain check
    chain_ok = False
    chain_name = ""
    try:
        res = requests.get(f"{settings.BLOCKCHAIN_NODE_URL}/blockchain", timeout=3)
        if res.ok:
            chain = res.json().get("chain", [])
            for block in chain:
                for item in block.get("data", []):
                    if str(item.get("product_id", "")).strip() == pid:
                        chain_ok = True
                        chain_name = str(item.get("name", "") or "")
                        break
                if chain_ok:
                    break
    except Exception:
        pass

    status = ScanLog.STATUS_FAKE
    if product and db_hash_ok:
        status = ScanLog.STATUS_AUTHENTIC
    elif chain_ok:
        status = ScanLog.STATUS_AUTHENTIC

    ScanLog.objects.create(
        product_id=pid,
        status=status,
        user=request.user,
        client_ip=_get_client_ip(request),
        product_name=(product.product_name if product else chain_name),
        category=(product.category if product else ""),
        manufacturer_name=(product.manufacturer_name if product else ""),
    )

    if status != ScanLog.STATUS_AUTHENTIC:
        return JsonResponse({"status": status, "product_id": pid, "reason": "No matching product/hash found."})

    if product:
        return JsonResponse(
            {
                "status": status,
                "product_id": pid,
                "product_name": product.product_name,
                "category": product.category,
                "manufacturer_name": product.manufacturer_name,
                "hash_value": product.hash_value,
            }
        )

    return JsonResponse({"status": status, "product_id": pid, "product_name": chain_name})

# -----------------------------
# Auth
# -----------------------------
def register(request: HttpRequest):
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        role = (request.POST.get("role") or User.ROLE_CUSTOMER).strip()

        if not username or not password:
            return render(request, "register.html", {"error": "Username and password are required."})

        if role not in {User.ROLE_ADMIN, User.ROLE_MANUFACTURER, User.ROLE_CUSTOMER}:
            role = User.ROLE_CUSTOMER

        if User.objects.filter(username=username).exists():
            return render(request, "register.html", {"error": "Username already exists."})

        User.objects.create_user(username=username, password=password, role=role, is_active=True)
        messages.success(request, "Registration successful. Please login.")
        return redirect("login")

    return render(request, "register.html")


def user_login(request: HttpRequest):
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.role == User.ROLE_ADMIN:
                return redirect("admin_dashboard")
            if user.role == User.ROLE_MANUFACTURER:
                return redirect("manufacturer_dashboard")
            return redirect("verify")

        return render(request, "login.html", {"error": "Invalid credentials."})

    return render(request, "login.html")


def user_logout(request: HttpRequest):
    logout(request)
    return redirect("login")


# -----------------------------
# Dashboards
# -----------------------------
@login_required
@role_required(User.ROLE_ADMIN)
def admin_dashboard(request: HttpRequest):
    return render(request, "admin_dashboard.html", {"active_tab": "admin"})


@login_required
@role_required(User.ROLE_MANUFACTURER)
def manufacturer_dashboard(request: HttpRequest):
    return render(request, "manufacturer_dashboard.html", {"active_tab": "manufacturer"})


# -----------------------------
# Admin module (custom UI)
# -----------------------------
@login_required
@role_required(User.ROLE_ADMIN)
def manage_users(request: HttpRequest):
    users = User.objects.all().order_by("username")
    return render(request, "admin_manage_users.html", {"users": users, "active_tab": "admin"})


@login_required
@role_required(User.ROLE_ADMIN)
def add_user(request: HttpRequest):
    if request.method == "POST":
        form = AdminCreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User created successfully.")
            return redirect("manage_users")
    else:
        form = AdminCreateUserForm(initial={"is_active": True})

    return render(request, "admin_add_user.html", {"form": form, "active_tab": "admin"})


@login_required
@role_required(User.ROLE_ADMIN)
def toggle_user_active(request: HttpRequest, user_id: int):
    user = get_object_or_404(User, pk=user_id)

    if request.user.pk == user.pk:
        messages.error(request, "You cannot disable your own account.")
        return redirect("manage_users")

    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])
    return redirect("manage_users")


# -----------------------------
# Manufacturer module
# -----------------------------
@login_required
@role_required(User.ROLE_MANUFACTURER)
def register_product(request: HttpRequest):
    if request.method == "GET":
        return render(request, "manufacturer_register_product.html", {"active_tab": "manufacturer"})

    product_id = (request.POST.get("product_id") or "").strip()
    product_name = (request.POST.get("product_name") or "").strip()
    category = (request.POST.get("category") or "").strip()

    if not product_id or not product_name or not category:
        return render(
            request,
            "manufacturer_register_product.html",
            {"active_tab": "manufacturer", "error": "Product Id, Product Name, Category are required."},
        )

    if Product.objects.filter(product_id=product_id).exists():
        return render(
            request,
            "manufacturer_register_product.html",
            {"active_tab": "manufacturer", "error": "Product ID already exists."},
        )

    # 1) Store in DB (auto SHA-256 + QR happens in Product.save())
    product = Product.objects.create(
        product_id=product_id,
        product_name=product_name,
        category=category,
        manufacturer_user=request.user,
        manufacturer_name=request.user.username,
    )

    # 2) Store in blockchain (Node) + mine block
    node_ok = False
    node_error = None
    try:
            requests.post(f"{settings.BLOCKCHAIN_NODE_URL}/product",
            json={"product_id": product.product_id, "name": product.product_name},
            timeout=5,
        ).raise_for_status()

            requests.get(f"{settings.BLOCKCHAIN_NODE_URL}/mine", timeout=8).raise_for_status()
            node_ok = True
    except Exception as e:
        node_error = str(e)

    if node_ok:
        messages.success(request, "Product registered, QR generated, and stored in blockchain.")
    else:
        # Product is still registered in DB; only blockchain failed
        messages.warning(
            request,
            f"Product registered and QR generated, but blockchain update failed: {node_error}",
        )

    return redirect("my_products")

@login_required
def product_qr(request, product_id: str):
    p = get_object_or_404(Product, product_id=product_id)

    # QR payload matches your spec: product_id|sha256
    payload = f"{p.product_id}|{p.hash_value}"

    img = qrcode.make(payload)
    buf = BytesIO()
    img.save(buf, format="PNG")

    return HttpResponse(buf.getvalue(), content_type="image/png")
    
@login_required
@role_required(User.ROLE_MANUFACTURER)
def my_products(request: HttpRequest):
    products = Product.objects.filter(manufacturer_user=request.user).order_by("-created_at")
    return render(request, "manufacturer_my_products.html", {"active_tab": "manufacturer", "products": products})


@login_required
@role_required(User.ROLE_MANUFACTURER)
def generated_qrs(request: HttpRequest):
    products = Product.objects.filter(manufacturer_user=request.user).order_by("-created_at")
    return render(request, "manufacturer_generated_qrs.html", {"active_tab": "manufacturer", "products": products})
