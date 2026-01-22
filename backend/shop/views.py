import json
import os
from datetime import date, timedelta

from django.db import models
from django.db.models.functions import TruncDate
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Product, Order, OrderItem, User, Admin


ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "changemeadmin")

def home(request):
    """Tiny landing page so visiting http://127.0.0.1:8000/ doesn't 404."""
    data = {
        "service": "mini-shop-backend",
        "routes": {
            "api_base": "/api/",
            "products": "/api/products/",
            "django_admin": "/admin/",
        },
        "note": "Frontend is served separately from /frontend (e.g. python -m http.server 5500).",
    }
    return corsify(JsonResponse(data), request)


def corsify(response: HttpResponse, request=None) -> HttpResponse:
    """Attach permissive CORS headers so the static frontend can call the API."""
    origin = "*"
    if request and request.headers.get("Origin"):
        origin = request.headers["Origin"]

    response["Access-Control-Allow-Origin"] = origin
    response["Access-Control-Allow-Credentials"] = "true"
    response["Access-Control-Allow-Headers"] = "Content-Type, X-Admin-Token"
    response["Access-Control-Allow-Methods"] = "GET, POST, PATCH, DELETE, OPTIONS"
    return response


def parse_json(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return {}


def ensure_admin(request):
    token = request.headers.get("X-Admin-Token")
    return token == ADMIN_TOKEN


def handle_options(request):
    resp = JsonResponse({"ok": True})
    return corsify(resp, request)


def serialize_product(product: Product):
    uploaded_image_url = product.image.url if product.image else None
    effective_image_url = uploaded_image_url or product.image_url
    return {
        "id": product.id,
        "name": product.name,
        "price": float(product.price),
        "description": product.description,
        "image_url": effective_image_url,
        "uploaded_image_url": uploaded_image_url,
        "stock": product.stock,
    }


def serialize_order(order: Order):
    return {
        "order_id": str(order.public_id),
        "customer_name": order.customer_name,
        "customer_email": order.customer_email,
        "status": order.status,
        "estimated_delivery": order.estimated_delivery.isoformat() if order.estimated_delivery else None,
        "created_at": order.created_at.isoformat(),
        "total": order.total_amount,
        "items": [
            {
                "product_name": item.product_name,
                "quantity": item.quantity,
                "price_per_unit": float(item.price_per_unit),
                "subtotal": item.subtotal,
            }
            for item in order.items.all()
        ],
    }


@csrf_exempt
def products(request):
    if request.method == "OPTIONS":
        return handle_options(request)

    if request.method == "GET":
        data = [serialize_product(p) for p in Product.objects.all().order_by("id")]
        return corsify(JsonResponse(data, safe=False), request)

    if request.method == "POST":
        if not ensure_admin(request):
            return corsify(JsonResponse({"detail": "Admin token required."}, status=401), request)
        payload = parse_json(request)
        product = Product.objects.create(
            name=payload.get("name", "New Product"),
            price=payload.get("price", 0),
            description=payload.get("description", ""),
            image_url=payload.get("image_url", ""),
            stock=payload.get("stock", 0),
        )
        return corsify(JsonResponse(serialize_product(product), status=201), request)

    return corsify(JsonResponse({"detail": "Method not allowed."}, status=405), request)


@csrf_exempt
def product_detail(request, product_id: int):
    if request.method == "OPTIONS":
        return handle_options(request)

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return corsify(JsonResponse({"detail": "Product not found."}, status=404), request)

    if request.method == "GET":
        return corsify(JsonResponse(serialize_product(product)), request)

    if request.method in ("PUT", "PATCH"):
        if not ensure_admin(request):
            return corsify(JsonResponse({"detail": "Admin token required."}, status=401), request)
        payload = parse_json(request)
        for field in ["name", "price", "description", "image_url", "stock"]:
            if field in payload:
                setattr(product, field, payload[field])
        product.save()
        return corsify(JsonResponse(serialize_product(product)), request)

    if request.method == "DELETE":
        if not ensure_admin(request):
            return corsify(JsonResponse({"detail": "Admin token required."}, status=401), request)
        product.delete()
        return corsify(JsonResponse({"deleted": True}), request)

    return corsify(JsonResponse({"detail": "Method not allowed."}, status=405), request)


@csrf_exempt
def product_upload_image(request, product_id: int):
    """Admin-only endpoint to upload a product image using multipart form-data."""
    if request.method == "OPTIONS":
        return handle_options(request)

    if request.method != "POST":
        return corsify(JsonResponse({"detail": "Method not allowed."}, status=405), request)

    if not ensure_admin(request):
        return corsify(JsonResponse({"detail": "Admin token required."}, status=401), request)

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return corsify(JsonResponse({"detail": "Product not found."}, status=404), request)

    uploaded = request.FILES.get("image")
    if not uploaded:
        return corsify(JsonResponse({"detail": "No file found. Send multipart field 'image'."}, status=400), request)

    product.image = uploaded
    product.save()
    return corsify(JsonResponse(serialize_product(product)), request)


@csrf_exempt
def cart(request):
    if request.method == "OPTIONS":
        return handle_options(request)

    # Store cart in session: {"product_id": quantity}
    cart_data = request.session.get("cart", {})

    if request.method == "GET":
        items = []
        total = 0
        for product_id, qty in cart_data.items():
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                continue
            subtotal = float(product.price) * qty
            items.append(
                {
                    "product_id": product.id,
                    "name": product.name,
                    "price": float(product.price),
                    "quantity": qty,
                    "subtotal": subtotal,
                    "image_url": product.image_url,
                }
            )
            total += subtotal
        return corsify(JsonResponse({"items": items, "total": total}), request)

    payload = parse_json(request)
    product_id = str(payload.get("product_id"))
    quantity = int(payload.get("quantity", 1))

    if request.method == "POST":
        # Add item
        # Basic stock guard (demo-level)
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return corsify(JsonResponse({"detail": "Product not found."}, status=404), request)

        if product.stock <= 0:
            return corsify(JsonResponse({"detail": "Out of stock."}, status=400), request)

        cart_data[product_id] = cart_data.get(product_id, 0) + max(quantity, 1)
        request.session["cart"] = cart_data
        request.session.save()
        return corsify(JsonResponse({"updated": True, "cart": cart_data}), request)

    if request.method == "PATCH":
        if product_id in cart_data:
            if quantity <= 0:
                cart_data.pop(product_id, None)
            else:
                cart_data[product_id] = quantity
            request.session["cart"] = cart_data
            request.session.save()
        return corsify(JsonResponse({"updated": True, "cart": cart_data}), request)

    if request.method == "DELETE":
        cart_data.pop(product_id, None)
        request.session["cart"] = cart_data
        request.session.save()
        return corsify(JsonResponse({"updated": True, "cart": cart_data}), request)

    return corsify(JsonResponse({"detail": "Method not allowed."}, status=405), request)


@csrf_exempt
def checkout(request):
    if request.method == "OPTIONS":
        return handle_options(request)

    if request.method != "POST":
        return corsify(JsonResponse({"detail": "Method not allowed."}, status=405), request)

    payload = parse_json(request)
    customer_name = payload.get("name")
    customer_email = payload.get("email")
    cart_data = request.session.get("cart", {})

    if not customer_name or not customer_email:
        return corsify(JsonResponse({"detail": "Name and email are required."}, status=400), request)

    if not cart_data:
        return corsify(JsonResponse({"detail": "Cart is empty."}, status=400), request)

    order = Order.objects.create(
        customer_name=customer_name,
        customer_email=customer_email,
        status="Order Placed",
        estimated_delivery=date.today() + timedelta(days=5),
    )

    for product_id, qty in cart_data.items():
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            continue
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            quantity=qty,
            price_per_unit=product.price,
        )
        # Reduce stock but do not allow negative values
        product.stock = max(product.stock - qty, 0)
        product.save()

    # Clear cart after checkout
    request.session["cart"] = {}
    request.session.save()

    response_data = {
        "order_id": str(order.public_id),
        "status": order.status,
        "estimated_delivery": order.estimated_delivery.isoformat() if order.estimated_delivery else None,
    }
    return corsify(JsonResponse(response_data, status=201), request)


@csrf_exempt
def orders(request):
    if request.method == "OPTIONS":
        return handle_options(request)

    if not ensure_admin(request):
        return corsify(JsonResponse({"detail": "Admin token required."}, status=401), request)

    if request.method == "GET":
        data = [serialize_order(o) for o in Order.objects.all().order_by("-created_at")]
        return corsify(JsonResponse(data, safe=False), request)

    return corsify(JsonResponse({"detail": "Method not allowed."}, status=405), request)


@csrf_exempt
def daily_orders(request):
    if request.method == "OPTIONS":
        return handle_options(request)

    if not ensure_admin(request):
        return corsify(JsonResponse({"detail": "Admin token required."}, status=401), request)

    counts = (
        Order.objects.annotate(day=TruncDate("created_at"))
        .values("day")
        .order_by("day")
        .annotate(total=models.Count("id"))
    )
    data = [{"date": c["day"].isoformat() if c["day"] else None, "orders": c["total"]} for c in counts]
    return corsify(JsonResponse(data, safe=False), request)


@csrf_exempt
def user_signup(request):
    """Handle user signup."""
    if request.method == "OPTIONS":
        return handle_options(request)

    if request.method != "POST":
        return corsify(JsonResponse({"detail": "Method not allowed."}, status=405), request)

    payload = parse_json(request)
    username = payload.get("username", "").strip()
    password = payload.get("password", "").strip()
    email = payload.get("email", "").strip()

    if not username or not password:
        return corsify(JsonResponse({"detail": "Username and password are required."}, status=400), request)

    if User.objects.filter(username=username).exists():
        return corsify(JsonResponse({"detail": "Username already exists."}, status=400), request)

    if email and User.objects.filter(email=email).exists():
        return corsify(JsonResponse({"detail": "Email already exists."}, status=400), request)

    user = User(username=username, email=email if email else None)
    user.set_password(password)
    user.save()

    return corsify(JsonResponse({"success": True, "message": "User registered successfully.", "user_id": user.id}), request)


@csrf_exempt
def user_login(request):
    """Handle user login."""
    if request.method == "OPTIONS":
        return handle_options(request)

    if request.method != "POST":
        return corsify(JsonResponse({"detail": "Method not allowed."}, status=405), request)

    payload = parse_json(request)
    username = payload.get("username", "").strip()
    password = payload.get("password", "").strip()

    if not username or not password:
        return corsify(JsonResponse({"detail": "Username and password are required."}, status=400), request)

    try:
        user = User.objects.get(username=username)
        if user.check_password(password):
            return corsify(JsonResponse({"success": True, "message": "Login successful.", "user_id": user.id}), request)
        else:
            return corsify(JsonResponse({"detail": "Invalid credentials."}, status=401), request)
    except User.DoesNotExist:
        return corsify(JsonResponse({"detail": "User not found."}, status=404), request)


@csrf_exempt
def admin_login(request):
    """Handle admin login."""
    if request.method == "OPTIONS":
        return handle_options(request)

    if request.method != "POST":
        return corsify(JsonResponse({"detail": "Method not allowed."}, status=405), request)

    payload = parse_json(request)
    username = payload.get("username", "").strip()
    password = payload.get("password", "").strip()

    if not username or not password:
        return corsify(JsonResponse({"detail": "Username and password are required."}, status=400), request)

    try:
        admin = Admin.objects.get(username=username)
        if admin.check_password(password):
            return corsify(JsonResponse({"success": True, "message": "Admin login successful.", "admin_id": admin.id}), request)
        else:
            return corsify(JsonResponse({"detail": "Invalid credentials."}, status=401), request)
    except Admin.DoesNotExist:
        return corsify(JsonResponse({"detail": "Admin not found."}, status=404), request)


def redirect_to_error(request, code=500, title="Something Went Wrong", message="An unexpected error occurred.", details=""):
    """Helper function to redirect to error page with parameters."""
    from urllib.parse import urlencode
    
    params = {
        'code': code,
        'title': title,
        'message': message,
    }
    if details:
        params['details'] = details
    
    query_string = urlencode(params)
    from django.shortcuts import redirect
    return redirect(f'/error.html?{query_string}')


def handler404(request, exception):
    """Handle 404 - Page Not Found."""
    from django.shortcuts import redirect
    from urllib.parse import urlencode
    
    params = urlencode({
        'code': '404',
        'title': 'Page Not Found',
        'message': 'The page you are looking for does not exist or has been moved.',
        'details': f'Path: {request.path}'
    })
    return redirect(f'/error.html?{params}')


def handler500(request):
    """Handle 500 - Internal Server Error."""
    from django.shortcuts import redirect
    from urllib.parse import urlencode
    
    params = urlencode({
        'code': '500',
        'title': 'Internal Server Error',
        'message': 'An unexpected error occurred on the server.',
        'details': 'Please try again later or contact support.'
    })
    return redirect(f'/error.html?{params}')


def handler403(request, exception=None):
    """Handle 403 - Forbidden."""
    from django.shortcuts import redirect
    from urllib.parse import urlencode
    
    params = urlencode({
        'code': '403',
        'title': 'Access Forbidden',
        'message': 'You do not have permission to access this resource.',
        'details': 'Contact administrator if you believe this is a mistake.'
    })
    return redirect(f'/error.html?{params}')


def handler401(request, exception=None):
    """Handle 401 - Unauthorized."""
    from django.shortcuts import redirect
    from urllib.parse import urlencode
    
    params = urlencode({
        'code': '401',
        'title': 'Unauthorized',
        'message': 'Authentication is required to access this resource.',
        'details': 'Please log in to continue.'
    })
    return redirect(f'/error.html?{params}')
