"""
توابع دکوراتور امن برای استفاده در views
دکوراتورهای پیشرفته برای مدیریت دسترسی‌ها و امنیت سیستم
"""

import functools
import logging
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test, login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponseForbidden
from django.conf import settings

# تنظیم لاگر امنیتی
security_logger = logging.getLogger('security')

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

def authenticated_user_required(view_func=None, custom_forbidden_template=None):
    """
    دکوراتور پیشرفته برای دسترسی کاربران احراز هویت شده
    با امکان نمایش صفحه خطای سفارشی 403
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                # ثبت تلاش دسترسی غیرمجاز
                security_logger.warning(
                    f"Unauthorized access attempt: {request.path}",
                    extra={
                        'ip': _get_client_ip(request),
                        'user': 'anonymous',
                        'path': request.path
                    }
                )
                
                # نمایش صفحه خطای فوربیدن شخصی‌سازی شده
                if custom_forbidden_template:
                    return render(request, custom_forbidden_template, {
                        'message': 'برای دسترسی به این صفحه باید وارد سیستم شوید.',
                        'login_url': f"{reverse('accounts:login')}?next={request.path}"
                    }, status=403)
                
                # نمایش صفحه خطای فوربیدن پیش‌فرض
                return render(request, 'errors/403.html', {
                    'message': 'برای دسترسی به این صفحه باید وارد سیستم شوید.',
                    'login_url': f"{reverse('accounts:login')}?next={request.path}"
                }, status=403)
            
            # در صورت احراز هویت، اجرای ویو اصلی
            return view_func(request, *args, **kwargs)
        
        return wrapper
    
    if view_func:
        return decorator(view_func)
    return decorator

def admin_access_required(view_func=None, custom_forbidden_template=None):
    """
    دکوراتور پیشرفته برای دسترسی مدیران سیستم
    با نمایش صفحه خطای سفارشی 403
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # بررسی احراز هویت و دسترسی مدیران
            if not request.user.is_authenticated:
                # ثبت تلاش دسترسی غیرمجاز
                security_logger.warning(
                    f"Unauthorized admin access attempt: {request.path}",
                    extra={
                        'ip': _get_client_ip(request),
                        'user': 'anonymous',
                        'path': request.path
                    }
                )
                
                # نمایش صفحه خطای فوربیدن شخصی‌سازی شده
                return render(request, 'errors/403.html', {
                    'message': 'برای دسترسی به این صفحه باید وارد سیستم شوید.',
                    'login_url': f"{reverse('accounts:login')}?next={request.path}"
                }, status=403)
            
            # بررسی دسترسی مدیران - با بررسی جامع‌تر
            user = request.user
            
            # بررسی از طریق گروه‌های سیستم
            is_in_admin_group = user.groups.filter(name__in=['admin_super', 'admin_property', 'admin_sales']).exists()
            
            # بررسی از طریق فیلدهای داخلی جنگو
            is_admin_via_django = user.is_staff or user.is_superuser
            
            # بررسی از طریق پروفایل (اگر وجود داشته باشد)
            is_admin_via_profile = False
            if hasattr(user, 'profile'):
                profile = user.profile
                if hasattr(profile, 'is_super_admin') and profile.is_super_admin:
                    is_admin_via_profile = True
                elif hasattr(profile, 'is_property_manager') and profile.is_property_manager:
                    is_admin_via_profile = True
                elif hasattr(profile, 'is_sales_agent') and profile.is_sales_agent:
                    is_admin_via_profile = True
            
            # اگر با هیچکدام از روش‌ها تایید نشد، دسترسی ندارد
            if not (is_in_admin_group or is_admin_via_django or is_admin_via_profile):
                # ثبت تلاش دسترسی غیرمجاز
                security_logger.warning(
                    f"Insufficient permissions for admin access: {request.path}",
                    extra={
                        'ip': _get_client_ip(request),
                        'user': request.user.username,
                        'path': request.path,
                        'groups': [g.name for g in request.user.groups.all()]
                    }
                )
                
                # نمایش صفحه خطای فوربیدن شخصی‌سازی شده
                if custom_forbidden_template:
                    return render(request, custom_forbidden_template, {
                        'message': 'شما مجوز دسترسی به این بخش را ندارید.',
                        'title': 'خطای دسترسی',
                        'code': 403
                    }, status=403)
                
                # نمایش صفحه خطای فوربیدن پیش‌فرض
                from hiro_estate.security_views import custom_permission_denied
                return custom_permission_denied(request)
            
            # در صورت داشتن دسترسی، اجرای ویو اصلی
            return view_func(request, *args, **kwargs)
        
        return wrapper
    
    if view_func:
        return decorator(view_func)
    return decorator

def public_access_only(allowed_pages=None):
    """
    دکوراتور برای مشخص کردن صفحات با دسترسی عمومی
    سایر صفحات به صورت خودکار نیاز به احراز هویت خواهند داشت
    
    :param allowed_pages: لیست مسیرهای URL که دسترسی عمومی دارند (بدون نیاز به لاگین)
    """
    if allowed_pages is None:
        allowed_pages = ['/', '/accounts/login/', '/accounts/logout/']
    
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # اگر صفحه در لیست صفحات عمومی باشد، اجازه دسترسی می‌دهیم
            if request.path in allowed_pages:
                return view_func(request, *args, **kwargs)
            
            # در غیر این صورت، نیاز به احراز هویت داریم
            if not request.user.is_authenticated:
                # ثبت تلاش دسترسی غیرمجاز
                security_logger.info(
                    f"Redirecting unauthenticated user to login: {request.path}",
                    extra={
                        'ip': _get_client_ip(request),
                        'path': request.path
                    }
                )
                
                # هدایت به صفحه لاگین
                return redirect(f"{reverse('accounts:login')}?next={request.path}")
            
            # کاربر احراز هویت شده، اجازه دسترسی دارد
            return view_func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator

def _get_client_ip(request):
    """دریافت IP واقعی کاربر"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip