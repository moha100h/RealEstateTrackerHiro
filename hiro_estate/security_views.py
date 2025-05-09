"""
نمای‌های امنیتی سیستم هیرو املاک
برای مدیریت خطاهای HTTP و لاگ کردن رویدادهای امنیتی
"""

import json
import logging
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings

# لاگر امنیتی
security_logger = logging.getLogger('security')

def custom_permission_denied(request, exception=None):
    """
    صفحه خطای سفارشی 403 (دسترسی غیرمجاز)
    """
    security_logger.warning(
        f"Access denied to {request.path}",
        extra={
            'user': request.user.username if request.user.is_authenticated else 'anonymous',
            'ip': _get_client_ip(request),
            'path': request.path
        }
    )
    
    # در حالت API، پاسخ JSON برمی‌گرداند
    if request.headers.get('Content-Type') == 'application/json' or \
       request.headers.get('Accept') == 'application/json':
        return JsonResponse({
            'status': 'error',
            'code': 403,
            'message': 'دسترسی به این صفحه یا عملیات امکان‌پذیر نیست.'
        }, status=403)
    
    # در حالت معمولی، صفحه HTML برمی‌گرداند
    context = {
        'status_code': 403,
        'error_message': 'شما اجازه دسترسی به این بخش را ندارید',
    }
    response = render(request, 'errors/403.html', context, status=403)
    return response

def custom_page_not_found(request, exception=None):
    """
    صفحه خطای سفارشی 404 (صفحه یافت نشد)
    """
    if settings.DEBUG:
        security_logger.info(
            f"Page not found: {request.path}",
            extra={
                'user': request.user.username if request.user.is_authenticated else 'anonymous',
                'ip': _get_client_ip(request),
                'path': request.path
            }
        )
    
    # در حالت API، پاسخ JSON برمی‌گرداند
    if request.headers.get('Content-Type') == 'application/json' or \
       request.headers.get('Accept') == 'application/json':
        return JsonResponse({
            'status': 'error',
            'code': 404,
            'message': 'صفحه یا منبع درخواستی یافت نشد.'
        }, status=404)
    
    # در حالت معمولی، صفحه HTML برمی‌گرداند
    context = {
        'status_code': 404,
        'error_message': 'صفحه مورد نظر یافت نشد',
    }
    response = render(request, 'errors/404.html', context, status=404)
    return response

def custom_server_error(request, exception=None):
    """
    صفحه خطای سفارشی 500 (خطای سرور)
    """
    if settings.DEBUG and exception:
        security_logger.error(
            f"Server error at {request.path}: {str(exception)}",
            exc_info=True,
            extra={
                'user': request.user.username if request.user.is_authenticated else 'anonymous',
                'ip': _get_client_ip(request),
                'path': request.path
            }
        )
    else:
        security_logger.error(
            f"Server error at {request.path}",
            exc_info=True,
            extra={
                'user': request.user.username if request.user.is_authenticated else 'anonymous',
                'ip': _get_client_ip(request),
                'path': request.path
            }
        )
    
    # در حالت API، پاسخ JSON برمی‌گرداند
    if request.headers.get('Content-Type') == 'application/json' or \
       request.headers.get('Accept') == 'application/json':
        return JsonResponse({
            'status': 'error',
            'code': 500,
            'message': 'خطایی در سرور رخ داده است. لطفاً بعداً دوباره تلاش کنید.'
        }, status=500)
    
    # در حالت معمولی، صفحه HTML برمی‌گرداند
    context = {
        'status_code': 500,
        'error_message': 'خطایی در سرور رخ داده است',
    }
    response = render(request, 'errors/500.html', context, status=500)
    return response

def security_error_handler(request):
    """
    هدایت‌کننده خطاهای امنیتی به صفحات مناسب
    """
    error_type = request.GET.get('type', 'forbidden')
    
    if error_type == 'forbidden':
        return custom_permission_denied(request)
    elif error_type == 'not_found':
        return custom_page_not_found(request)
    else:
        return custom_server_error(request)

@csrf_exempt
@require_POST
def csp_report_view(request):
    """
    دریافت گزارش‌های نقض CSP (Content Security Policy)
    """
    try:
        csp_report = json.loads(request.body.decode('utf-8'))
        security_logger.warning(
            "CSP Violation",
            extra={
                'report': csp_report.get('csp-report', {}),
                'user': request.user.username if request.user.is_authenticated else 'anonymous',
                'ip': _get_client_ip(request)
            }
        )
    except Exception as e:
        security_logger.error(f"Error processing CSP report: {e}", exc_info=True)
    
    return HttpResponse()

def security_headers_test_view(request):
    """
    نمایش هدرهای امنیتی سرور (فقط برای محیط توسعه)
    """
    if not settings.DEBUG:
        return HttpResponseForbidden(b"This page is only available in DEBUG mode")
    
    response = HttpResponse(b"""
    <html>
    <head><title>Security Headers Test</title></head>
    <body>
        <h1>Security Headers Test</h1>
        <p>Check the response headers to see the security headers configured on this server.</p>
        <h2>Common Security Headers</h2>
        <ul>
            <li>Content-Security-Policy</li>
            <li>X-Content-Type-Options</li>
            <li>X-Frame-Options</li>
            <li>X-XSS-Protection</li>
            <li>Strict-Transport-Security</li>
            <li>Referrer-Policy</li>
            <li>Feature-Policy</li>
        </ul>
    </body>
    </html>
    """)
    
    # هدرهای امنیتی استاندارد
    response['X-Content-Type-Options'] = 'nosniff'
    response['X-Frame-Options'] = 'SAMEORIGIN'
    response['X-XSS-Protection'] = '1; mode=block'
    response['Referrer-Policy'] = 'same-origin'
    
    # فقط در HTTPS اضافه می‌شود
    if settings.USE_HTTPS:
        response['Strict-Transport-Security'] = f'max-age={settings.SECURE_HSTS_SECONDS}; includeSubDomains; preload'

    return response

def _get_client_ip(request):
    """دریافت IP واقعی کاربر"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip