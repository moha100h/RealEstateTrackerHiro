"""
اسکریپت برای اضافه کردن یک کاربر موجود به گروه‌های مدیریت سیستم
"""

import os
import django
import sys

# تنظیم محیط جنگو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hiro_estate.settings')
django.setup()

# وارد کردن مدل‌ها بعد از تنظیم جنگو
from django.contrib.auth.models import User, Group

def add_user_to_admin_groups(username):
    """
    اضافه کردن کاربر با نام کاربری مشخص شده به گروه‌های مدیریت
    """
    try:
        # پیدا کردن کاربر با نام کاربری مشخص شده
        user = User.objects.get(username=username)
        
        # پیدا کردن گروه‌های مدیریت
        admin_super = Group.objects.get(name='admin_super')
        property_manager = Group.objects.get(name='admin_property')
        sales_agent = Group.objects.get(name='admin_sales')
        
        # اضافه کردن کاربر به گروه‌ها
        user.groups.add(admin_super)
        user.groups.add(property_manager)
        user.groups.add(sales_agent)
        
        # اطمینان از فعال بودن کاربر
        if not user.is_active:
            user.is_active = True
            user.save()
            
        print(f"کاربر '{username}' با موفقیت به همه گروه‌های مدیریت اضافه شد.")
        
    except User.DoesNotExist:
        print(f"خطا: کاربر با نام کاربری '{username}' یافت نشد.")
    except Group.DoesNotExist:
        print("خطا: یک یا چند گروه مدیریت یافت نشد. لطفاً ابتدا گروه‌ها را ایجاد کنید.")
    except Exception as e:
        print(f"خطای غیرمنتظره: {str(e)}")

if __name__ == "__main__":
    # اگر نام کاربری از خط فرمان ارسال شده باشد
    if len(sys.argv) > 1:
        username = sys.argv[1]
        add_user_to_admin_groups(username)
    else:
        # اگر نام کاربری ارسال نشده باشد، از کاربر بپرس
        username = input("لطفاً نام کاربری کاربر مورد نظر را وارد کنید: ")
        add_user_to_admin_groups(username)