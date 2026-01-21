#!/usr/bin/env python
"""
Setup test data for the e-commerce application
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from shop.models import User, Admin, Product

# Create a test user
user, created = User.objects.get_or_create(username='testuser')
if created:
    user.set_password('password123')
    user.email = 'testuser@example.com'
    user.save()
    print("✓ Test user created: testuser / password123")
else:
    print("✓ Test user already exists: testuser / password123")

# Create a test admin
admin, created = Admin.objects.get_or_create(username='testadmin')
if created:
    admin.set_password('admin123')
    admin.email = 'admin@example.com'
    admin.save()
    print("✓ Test admin created: testadmin / admin123")
else:
    print("✓ Test admin already exists: testadmin / admin123")

# Create sample products if none exist
if Product.objects.count() == 0:
    products = [
        Product(name='Laptop', price=999.99, description='High-performance laptop', stock=5),
        Product(name='Mouse', price=29.99, description='Wireless mouse', stock=20),
        Product(name='Keyboard', price=79.99, description='Mechanical keyboard', stock=15),
    ]
    for p in products:
        p.save()
    print("✓ Sample products created")
else:
    print(f"✓ Products already exist ({Product.objects.count()} products)")
