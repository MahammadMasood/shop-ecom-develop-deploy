from django.urls import path
from . import views


urlpatterns = [
    path("products/", views.products, name="products"),
    path("products/<int:product_id>/", views.product_detail, name="product_detail"),
    path("products/<int:product_id>/upload-image/", views.product_upload_image, name="product_upload_image"),
    path("cart/", views.cart, name="cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("orders/", views.orders, name="orders"),
    path("analytics/daily-orders/", views.daily_orders, name="daily_orders"),
    path("user/signup/", views.user_signup, name="user_signup"),
    path("user/login/", views.user_login, name="user_login"),
    path("admin/login/", views.admin_login, name="admin_login"),
]

