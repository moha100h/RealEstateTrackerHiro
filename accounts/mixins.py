"""
میکسین‌های سفارشی برای کنترل دسترسی در سیستم هیرو املاک
"""

from typing import Any, cast, TYPE_CHECKING
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

if TYPE_CHECKING:
    from django.http import HttpRequest
    from django.contrib.auth.models import User

class CustomLoginRequiredMixin(LoginRequiredMixin):
    """
    میکسین سفارشی احراز هویت که در صورت عدم ورود کاربر به صفحه 403 هدایت می‌کند
    به جای هدایت به صفحه لاگین
    """
    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            # به جای هدایت به صفحه لاگین، خطای 403 (دسترسی غیرمجاز) نمایش داده می‌شود
            from hiro_estate.security_views import custom_permission_denied
            return custom_permission_denied(request)
        return super().dispatch(request, *args, **kwargs)

class SuperUserRequiredMixin(LoginRequiredMixin):
    """
    میکسین محدود کردن دسترسی به سوپر ادمین‌ها
    """
    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            from hiro_estate.security_views import custom_permission_denied
            return custom_permission_denied(request)
            
        if not request.user.is_superuser:
            from hiro_estate.security_views import custom_permission_denied
            return custom_permission_denied(request)
            
        return super().dispatch(request, *args, **kwargs)

class AdminRequiredMixin(LoginRequiredMixin):
    """
    میکسین محدود کردن دسترسی به مدیران سیستم
    """
    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            from hiro_estate.security_views import custom_permission_denied
            return custom_permission_denied(request)
        
        user = cast(User, request.user)
        is_admin = user.is_superuser or user.is_staff or (
            hasattr(user, 'profile') and 
            getattr(user.profile, 'is_super_admin', False)
        )
        
        if not is_admin:
            from hiro_estate.security_views import custom_permission_denied
            return custom_permission_denied(request)
        
        return super().dispatch(request, *args, **kwargs)

class PropertyManagerRequiredMixin(LoginRequiredMixin):
    """
    میکسین محدود کردن دسترسی به مدیران املاک
    """
    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            from hiro_estate.security_views import custom_permission_denied
            return custom_permission_denied(request)
        
        user = cast(User, request.user)
        is_property_manager = (
            user.is_superuser or 
            user.is_staff or 
            (hasattr(user, 'profile') and 
             (getattr(user.profile, 'is_super_admin', False) or 
              getattr(user.profile, 'is_property_manager', False)))
        )
        
        if not is_property_manager:
            from hiro_estate.security_views import custom_permission_denied
            return custom_permission_denied(request)
        
        return super().dispatch(request, *args, **kwargs)