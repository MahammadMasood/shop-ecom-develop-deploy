from django.db import models
from django.contrib.auth.hashers import make_password, check_password
import uuid


class User(models.Model):
    """Store user credentials for website signup/login."""
    
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    email = models.EmailField(unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self) -> str:
        return self.username
    
    def set_password(self, raw_password):
        """Hash and set the password."""
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        """Check if the provided password matches the stored hash."""
        return check_password(raw_password, self.password)


class Admin(models.Model):
    """Store admin credentials for admin login."""
    
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    email = models.EmailField(unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self) -> str:
        return self.username
    
    def set_password(self, raw_password):
        """Hash and set the password."""
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        """Check if the provided password matches the stored hash."""
        return check_password(raw_password, self.password)


class Product(models.Model):
    """Store product catalog data."""

    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    # Either upload an image (recommended) OR provide an external URL.
    image = models.ImageField(upload_to="products/", null=True, blank=True)
    image_url = models.URLField(blank=True)
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name


class Order(models.Model):
    """Customer orders created at checkout."""

    ORDER_STATUS_CHOICES = [
        ("Order Placed", "Order Placed"),
        ("Processing", "Processing"),
        ("Shipped", "Shipped"),
        ("Delivered", "Delivered"),
    ]

    # A human friendly immutable ID for customers/admins.
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    status = models.CharField(max_length=50, choices=ORDER_STATUS_CHOICES, default="Order Placed")
    estimated_delivery = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Order {self.public_id}"

    @property
    def total_amount(self) -> float:
        return sum(item.subtotal for item in self.items.all())


class OrderItem(models.Model):
    """Individual line items for an order.

    Product data is denormalized to keep history even if the product changes.
    """

    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self) -> float:
        return float(self.price_per_unit) * self.quantity

    def __str__(self) -> str:
        return f"{self.product_name} x {self.quantity}"
