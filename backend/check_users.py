import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from shop.models import User

print("=== ALL USERS IN DATABASE ===")
users = User.objects.all()
for user in users:
    print(f"ID: {user.id} | Username: {user.username} | Email: {user.email or 'N/A'}")

print(f"\nTotal Users: {users.count()}")
