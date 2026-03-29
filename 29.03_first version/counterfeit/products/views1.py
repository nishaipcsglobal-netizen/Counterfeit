from django.shortcuts import render
import requests
import qrcode
import os
from .models import Product
import hashlib
from django.http import JsonResponse
from django.conf import settings
import json
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth import authenticate, login, logout
from .models import User

from django.contrib.auth import logout
from django.shortcuts import redirect

from django.contrib.auth.decorators import login_required

@login_required
def admin_dashboard(request):
    return render(request, "admin_dashboard.html")


@login_required
def manufacturer_dashboard(request):
    return render(request, "manufacturer_dashboard.html")

def user_logout(request):
    logout(request)
    return redirect('/login/')

def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        role = request.POST.get("role")

        user = User.objects.create_user(
            username=username,
            password=password,
            role=role
        )

        return redirect('/login/')

    return render(request, "register.html")

def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)

            if user.role == "admin":
                return redirect('/admin-dashboard/')
            else:
                return redirect('/manufacturer-dashboard/')

    return render(request, "login.html")

def admin_dashboard(request):
    return render(request, "admin_dashboard.html")


def manufacturer_dashboard(request):
    return render(request, "manufacturer_dashboard.html")


@csrf_exempt
def verify_api(request):
    if request.method == "POST":
        data = json.loads(request.body)
        product_id = data.get("product_id")

        try:
            # Call Node blockchain
            res = requests.get("http://localhost:3000/blockchain")
            chain = res.json()["chain"]

            for block in chain:
                for item in block["data"]:
                    if item["product_id"] == product_id:
                        return JsonResponse({
                            "status": "AUTHENTIC",
                            "product_id": product_id,
                            "name": item.get("name"),
                        })

            return JsonResponse({"status": "FAKE"})

        except Exception as e:
            return JsonResponse({"error": str(e)})

def verify_product(request):
    result = None
    
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        scanned_hash = request.POST.get("hash_value")

        try:
            product = Product.objects.get(product_id=product_id)

            data = f"{product.product_id}{product.product_name}{product.manufacturer}"
            recalculated_hash = hashlib.sha256(data.encode()).hexdigest()

            if recalculated_hash == scanned_hash:
                result = "Genuine Product"
            else:
                result = "Fake Product"

        except Product.DoesNotExist:
            result = "Product Not Found"

    return render(request, "verify.html", {"result": result})
    
    # file: app/views.py



def add_product_to_blockchain(request):
    if request.method =="GET":
        return render(request,"add_product.html")
    elif request.method == "POST":
        product_id = request.POST.get("product_id")
        name = request.POST.get("name")

        data = {
            "product_id": product_id,
            "name": name
        }

        try:
            # Step 1: Send product to Node
            res1 = requests.post("http://localhost:3000/product", json=data)

            # Step 2: Mine block
            res2 = requests.get("http://localhost:3000/mine")
            
            # Generate QR
            qr_folder = os.path.join(settings.MEDIA_ROOT, "qrcodes")
            os.makedirs(qr_folder, exist_ok=True)
            
            qr_filename = f"{product_id}.png"

            qr_path = os.path.join(qr_folder, f"{product_id}.png")

            img = qrcode.make(product_id)
            img.save(qr_path)
            qr_url = f"/media/qrcodes/{qr_filename}"

            return render(request, "result.html", {
                "product_id": product_id,
                "qr_url": qr_url
            })

            #print("Saving QR at:", qr_path)

            #return JsonResponse({
             #   "message": "Product added to blockchain + QR generated",
              #  "qr":f"/media/qrcodes/{product_id}.png"})
              #  "node_response": res1.json(),
              #  "mine_response": res2.json()
            #})

        except Exception as e:
            return JsonResponse({"error": str(e)})