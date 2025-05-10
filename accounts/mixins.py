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
        
        # بررسی از طریق گروه‌های سیستم
        is_in_admin_group = user.groups.filter(name__in=['admin_super', 'admin_property']).exists()
        
        # بررسی از طریق متد‌های پروفایل
        is_admin_via_profile = False
        if hasattr(user, 'profile'):
            profile = user.profile
            if hasattr(profile, 'is_super_admin') and profile.is_super_admin:
                is_admin_via_profile = True
            elif hasattr(profile, 'is_property_manager') and profile.is_property_manager:
                is_admin_via_profile = True
        
        # بررسی از طریق فیلد‌های داخلی جنگو
        is_admin_via_django = user.is_superuser or user.is_staff
        
        # اگر با هر یک از روش‌ها تایید شد، دسترسی بدهد
        if not (is_in_admin_group or is_admin_via_profile or is_admin_via_django):
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
        
        # بررسی از طریق گروه‌های سیستم - هم مدیران املاک و هم کارشناسان فروش
        is_in_property_group = user.groups.filter(name__in=['admin_super', 'admin_property', 'admin_sales']).exists()
        
        # بررسی از طریق متد‌های پروفایل
        is_property_manager_via_profile = False
        if hasattr(user, 'profile'):
            profile = user.profile
            if hasattr(profile, 'is_super_admin') and profile.is_super_admin:
                is_property_manager_via_profile = True
            elif hasattr(profile, 'is_property_manager') and profile.is_property_manager:
                is_property_manager_via_profile = True
            elif hasattr(profile, 'is_sales_agent') and profile.is_sales_agent:
                is_property_manager_via_profile = True
        
        # بررسی از طریق فیلد‌های داخلی جنگو
        is_property_manager_via_django = user.is_superuser or user.is_staff
        
        # اگر با هر یک از روش‌ها تایید شد، دسترسی بدهد
        if not (is_in_property_group or is_property_manager_via_profile or is_property_manager_via_django):
            from hiro_estate.security_views import custom_permission_denied
            return custom_permission_denied(request)
        
        return super().dispatch(request, *args, **kwargs)