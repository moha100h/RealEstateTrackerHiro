"""
Script to create initial data for the Hiro Real Estate system
"""

import os
import django

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hiro_estate.settings')
django.setup()

# Import models after Django setup
from django.contrib.auth.models import Group, Permission
from properties.models import PropertyType, TransactionType, PropertyStatus
from config.models import SystemConfig
from accounts.models import create_default_groups

# Create default user groups
print("Creating default user groups...")
create_default_groups()

# Create property types
print("Creating property types...")
property_types = [
    "آپارتمان",
    "ویلایی",
    "تجاری",
    "اداری",
    "زمین",
    "کلنگی"
]

for name in property_types:
    PropertyType.objects.get_or_create(name=name)

# Create transaction types
print("Creating transaction types...")
transaction_types = [
    "فروش",
    "اجاره",
    "رهن کامل",
    "رهن و اجاره",
    "پیش فروش",
    "مشارکت در ساخت"
]

for name in transaction_types:
    TransactionType.objects.get_or_create(name=name)

# Create property statuses
print("Creating property statuses...")
property_statuses = [
    "موجود",
    "فروخته شده",
    "اجاره داده شده",
    "رزرو شده",
    "در حال ساخت",
    "آماده تحویل"
]

for name in property_statuses:
    PropertyStatus.objects.get_or_create(name=name)

# Create system config if not exists
print("Creating system configuration...")
if not SystemConfig.objects.exists():
    SystemConfig.objects.create(
        website_title="سیستم هوشمند مدیریت املاک هیرو",
        font_type="vazir"
    )

print("Initial data creation completed successfully!")