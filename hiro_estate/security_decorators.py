"""
دکوراتورهای امنیتی سیستم هیرو املاک
برای کنترل دسترسی‌ها و امن‌سازی اجزای مختلف سیستم
"""

import logging
import functools
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse, resolve
from django.utils.decorators import method_decorator
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required, user_passes_test
from accounts.decorators import authenticated_user_required, admin_access_required

# تنظیم لاگر امنیتی
security_logger = logging.getLogger('security')

def admin_only_view(view_func=None):
    """
    دکوراتور برای محدود کردن صفحات به کاربران ادمین
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # بررسی اینکه آیا کاربر وارد شده است و ادمین است
            if not request.user.is_authenticated:
                return redirect(f"{reverse('accounts:login')}?next={request.path}")
            
            if not request.user.is_staff and not request.user.is_superuser:
                security_logger.warning(
                    f"Non-admin user tried to access admin-only page: {request.path}",
                    extra={
                        'user': request.user.username,
                        'ip': _get_client_ip(request),
                        'path': request.path
                    }
                )
                return redirect('hiro_estate.security_views.custom_permission_denied')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    
    if view_func:
        return decorator(view_func)
    return decorator


def access_control_middleware(get_response):
    """
    میدل‌ویر کنترل دسترسی صفحات
    محدود کردن دسترسی به صفحات بر اساس نوع کاربر
    """
    def middleware(request):
        # صفحاتی که نیاز به لاگین کاربر دارند
        path = request.path
        
        # بررسی صفحات مدیریتی (فقط مدیران)
        if any(path.startswith(admin_page) for admin_page in settings.ADMIN_ONLY_PAGES):
            if not request.user.is_authenticated:
                return redirect(f"{reverse('accounts:login')}?next={path}")
            
            if not request.user.is_staff and not request.user.is_superuser:
                security_logger.warning(
                    f"Non-admin user tried to access admin-only page: {path}",
                    extra={
                        'user': request.user.username,
                        'ip': _get_client_ip(request),
                        'path': path
                    }
                )
                from hiro_estate.security_views import custom_permission_denied
                return custom_permission_denied(request)
        
        # بررسی صفحات عمومی (استثناها)
        is_public_page = any(path.startswith(public_page) for public_page in settings.PUBLIC_PAGES)
        
        # اگر صفحه عمومی نیست و کاربر لاگین نشده است، هدایت به صفحه لاگین
        if not is_public_page and not request.user.is_authenticated:
            return redirect(f"{reverse('accounts:login')}?next={path}")
        
        response = get_response(request)
        return response
    
    return middleware


def staff_access_required(function=None, redirect_url=None):
    """
    دکوراتور برای محدود کردن دسترسی به کارکنان سیستم
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and (u.is_staff or u.is_superuser),
        login_url=redirect_url or 'accounts:login',
        redirect_field_name='next'
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def admin_access_required_class(cls):
    """
    دکوراتور برای کلاس‌های ویو که به دسترسی ادمین نیاز دارند
    برای استفاده روی کلاس‌های بر پایه Class-Based Views
    """
    view_decorator = admin_access_required(None)
    cls.dispatch = method_decorator(view_decorator)(cls.dispatch)
    return cls


def _get_client_ip(request):
    """دریافت IP واقعی کاربر"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip