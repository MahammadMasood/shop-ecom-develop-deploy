"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from shop import views as shop_views

urlpatterns = [
    # Frontend pages (served by Django so frontend+backend run on one server/port)
    path('', TemplateView.as_view(template_name="index.html"), name="home"),
    path('index.html', TemplateView.as_view(template_name="index.html"), name="home_index_html"),
    path('user-login.html', TemplateView.as_view(template_name="user-login.html"), name="user_login_page"),
    path('product.html', TemplateView.as_view(template_name="product.html"), name="product_page"),
    path('cart.html', TemplateView.as_view(template_name="cart.html"), name="cart_page"),
    path('checkout.html', TemplateView.as_view(template_name="checkout.html"), name="checkout_page"),
    path('order_confirmation.html', TemplateView.as_view(template_name="order_confirmation.html"), name="order_confirmation_page"),
    path('admin-ui.html', TemplateView.as_view(template_name="admin-ui.html"), name="admin_ui_page"),
    path('error.html', TemplateView.as_view(template_name="error.html"), name="error_page"),
    path('error-test.html', TemplateView.as_view(template_name="error-test.html"), name="error_test_page"),

    # Backend
    path('health/', shop_views.home),
    path('admin/', admin.site.urls),
    path('api/', include('shop.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Error handlers
handler404 = 'shop.views.handler404'
handler500 = 'shop.views.handler500'
handler403 = 'shop.views.handler403'
handler401 = 'shop.views.handler401'
