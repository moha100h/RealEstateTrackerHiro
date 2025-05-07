"""
توابع دکوراتور امن برای استفاده در views
"""

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test

def staff_required(view_func=None):
    """
    دکوراتور برای محدود کردن دسترسی به مدیران سیستم
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and (u.is_staff or u.is_superuser),
        login_url='accounts:login',
        redirect_field_name='next'
    )
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator

def superuser_required(view_func=None):
    """
    دکوراتور برای محدود کردن دسترسی فقط به مدیران ارشد (سوپرادمین)
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_superuser,
        login_url='accounts:login',
        redirect_field_name='next'
    )
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator