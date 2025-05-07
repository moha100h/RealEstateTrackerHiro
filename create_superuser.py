#!/usr/bin/env python
"""
Script to create a superuser for the Hiro Real Estate system
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hiro_estate.settings')
django.setup()

from django.contrib.auth.models import User
from django.db.utils import IntegrityError

def create_superuser():
    """Create a superuser for the system"""
    try:
        if not User.objects.filter(username='admin').exists():
            user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='مدیر',
                last_name='سیستم'
            )
            print(f"Superuser {user.username} created successfully!")
        else:
            print("Superuser 'admin' already exists.")
    except IntegrityError:
        print("Superuser 'admin' already exists.")
    except Exception as e:
        print(f"Error creating superuser: {e}")

if __name__ == "__main__":
    create_superuser()