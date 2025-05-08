"""
ویوهای امنیتی برای مدیریت خطاها و صفحات خطای سفارشی
"""

import logging
import json
from django.shortcuts import render
from django.http import HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError, JsonResponse
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# تنظیم لاگر امنیتی
security_logger = logging.getLogger('security')

def custom_permission_denied(request, exception=None):
    """
    صفحه خطای سفارشی 403 (دسترسی غیرمجاز)
    """
    # ثبت تلاش دسترسی غیرمجاز
    security_logger.warning(
        f"Access forbidden to path: {request.path}",
        extra={
            'ip': _get_client_ip(request),
            'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
            'path': request.path,
            'method': request.method,
            'referer': request.META.get('HTTP_REFERER', 'None'),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'None')
        }
    )
    
    context = {
        'title': 'خطای دسترسی',
        'message': 'شما مجوز لازم برای دسترسی به این صفحه را ندارید.',
        'code': 403,
        'login_url': f"{reverse('accounts:login')}?next={request.path}" if not request.user.is_authenticated else None
    }
    
    response = render(request, 'errors/403.html', context)
    response.status_code = 403
    return response


def custom_page_not_found(request, exception=None):
    """
    صفحه خطای سفارشی 404 (صفحه یافت نشد)
    """
    # ثبت درخواست صفحه نامعتبر
    security_logger.info(
        f"Page not found: {request.path}",
        extra={
            'ip': _get_client_ip(request),
            'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
            'path': request.path,
            'method': request.method,
            'referer': request.META.get('HTTP_REFERER', 'None')
        }
    )
    
    context = {
        'title': 'صفحه یافت نشد',
        'message': 'صفحه مورد نظر شما در سیستم وجود ندارد.',
        'code': 404
    }
    
    response = render(request, 'errors/404.html', context)
    response.status_code = 404
    return response


def custom_server_error(request, *args, **kwargs):
    """
    صفحه خطای سفارشی 500 (خطای سرور)
    """
    # ثبت خطای سرور
    security_logger.error(
        f"Server error for path: {request.path}",
        extra={
            'ip': _get_client_ip(request),
            'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
            'path': request.path,
            'method': request.method
        }
    )
    
    context = {
        'title': 'خطای سرور',
        'message': 'متأسفانه خطایی در سرور رخ داده است. لطفاً بعداً مجدداً تلاش کنید.',
        'code': 500
    }
    
    response = render(request, 'errors/500.html', context, status=500)
    return response


@csrf_exempt
@require_POST
def csp_report_view(request):
    """
    دریافت گزارش‌های نقض سیاست امنیت محتوا (CSP)
    """
    try:
        csp_report = json.loads(request.body.decode('utf-8'))
        security_logger.warning(
            "CSP Violation Report",
            extra={
                'ip': _get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
                'report': csp_report
            }
        )
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    
    return JsonResponse({'status': 'success'})


def security_headers_test_view(request):
    """
    صفحه تست هدرهای امنیتی (فقط در محیط توسعه)
    """
    return render(request, 'security/headers_test.html', {
        'title': 'تست هدرهای امنیتی',
        'headers': dict(request.headers)
    })


def security_error_handler(request, **kwargs):
    """
    هندلر خطاهای امنیتی
    بر اساس استاتوس کد، مسیردهی به صفحه خطای مناسب
    """
    status_code = kwargs.get('status_code', 500)
    exception = kwargs.get('exception', None)
    
    # بررسی نوع خطا
    if status_code == 403:
        return custom_permission_denied(request, exception)
    elif status_code == 404:
        return custom_page_not_found(request, exception)
    else:  # 500 و غیره
        return custom_server_error(request)


def _get_client_ip(request):
    """دریافت IP واقعی کاربر"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip