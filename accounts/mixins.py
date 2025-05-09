"""
میکسین‌های سفارشی برای کنترل دسترسی در سیستم هیرو املاک
"""

from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied

class CustomLoginRequiredMixin(AccessMixin):
    """
    میکسین سفارشی احراز هویت که در صورت عدم ورود کاربر به صفحه 403 هدایت می‌کند
    به جای هدایت به صفحه لاگین
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            # به جای هدایت به صفحه لاگین، خطای 403 (دسترسی غیرمجاز) نمایش داده می‌شود
            raise PermissionDenied("برای دسترسی به این صفحه باید وارد سیستم شوید.")
        return super().dispatch(request, *args, **kwargs)

class SuperUserRequiredMixin(AccessMixin):
    """
    میکسین محدود کردن دسترسی به سوپر ادمین‌ها
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("برای دسترسی به این صفحه باید وارد سیستم شوید.")
        if not request.user.is_superuser:
            raise PermissionDenied("فقط مدیران ارشد سیستم به این بخش دسترسی دارند.")
        return super().dispatch(request, *args, **kwargs)

class AdminRequiredMixin(AccessMixin):
    """
    میکسین محدود کردن دسترسی به مدیران سیستم
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("برای دسترسی به این صفحه باید وارد سیستم شوید.")
        
        is_admin = request.user.is_superuser or (
            hasattr(request.user, 'profile') and 
            request.user.profile.is_super_admin
        )
        
        if not is_admin:
            raise PermissionDenied("فقط مدیران سیستم به این بخش دسترسی دارند.")
        
        return super().dispatch(request, *args, **kwargs)

class PropertyManagerRequiredMixin(AccessMixin):
    """
    میکسین محدود کردن دسترسی به مدیران املاک
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("برای دسترسی به این صفحه باید وارد سیستم شوید.")
        
        is_property_manager = (request.user.is_superuser or 
            (hasattr(request.user, 'profile') and 
             (request.user.profile.is_super_admin or request.user.profile.is_property_manager))
        )
        
        if not is_property_manager:
            raise PermissionDenied("فقط مدیران املاک به این بخش دسترسی دارند.")
        
        return super().dispatch(request, *args, **kwargs)