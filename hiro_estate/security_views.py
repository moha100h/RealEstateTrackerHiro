"""
ویوهای مرتبط با امنیت سیستم
محافظت در برابر حملات سایبری و گزارش تخلفات امنیتی
"""
import json
import logging
import time
import ipaddress
import hashlib
import re
import os
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.core.cache import cache
from django.urls import reverse

# لاگر برای رویدادهای امنیتی
security_logger = logging.getLogger('security')

@csrf_exempt
@require_POST
def csp_report_view(request):
    """
    نقطه پایانی برای دریافت گزارش‌های نقض سیاست امنیت محتوا (CSP)
    """
    try:
        # تحلیل گزارش CSP از بدنه درخواست
        csp_report = json.loads(request.body.decode('utf-8'))
        
        # استخراج اطلاعات مربوطه
        document_uri = csp_report.get('csp-report', {}).get('document-uri', 'unknown')
        blocked_uri = csp_report.get('csp-report', {}).get('blocked-uri', 'unknown')
        violated_directive = csp_report.get('csp-report', {}).get('violated-directive', 'unknown')
        original_policy = csp_report.get('csp-report', {}).get('original-policy', 'unknown')
        
        # بررسی احراز هویت کاربر قبل از دسترسی به username
        username = 'anonymous'
        if hasattr(request, 'user') and request.user.is_authenticated:
            username = request.user.username
        
        # ثبت تخلف CSP با جزئیات مربوطه
        security_logger.warning(
            f"CSP Violation: {violated_directive} directive violated on {document_uri} by {blocked_uri}",
            extra={
                'ip': _get_client_ip(request),
                'user': username,
                'document_uri': document_uri,
                'blocked_uri': blocked_uri,
                'violated_directive': violated_directive,
                'original_policy': original_policy
            }
        )
        
        # اقدامات امنیتی اضافی - بررسی تکرار نقض از یک منبع
        ip_key = f"csp_violation:{_get_client_ip(request)}"
        violation_count = cache.get(ip_key, 0) + 1
        cache.set(ip_key, violation_count, 3600)  # ذخیره برای یک ساعت
        
        # اگر تعداد نقض‌ها از حد مجاز بیشتر باشد، شروع بررسی بیشتر
        if violation_count > 10:
            security_logger.error(
                f"Multiple CSP violations from IP: {_get_client_ip(request)}. Possible attack.",
                extra={
                    'ip': _get_client_ip(request),
                    'user': username,
                    'count': violation_count
                }
            )
            
            # در سیستم واقعی - ارسال هشدار به ادمین‌ها یا محدودیت دسترسی
        
        return HttpResponse(status=204)  # پاسخ بدون محتوا
    
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        security_logger.error(f"Failed to process CSP report: {str(e)}")
        return JsonResponse({'error': 'Invalid CSP report format'}, status=400)

@csrf_exempt
def security_headers_test_view(request):
    """
    ویو تست هدرهای امنیتی
    این فقط در حالت DEBUG قابل دسترسی است
    """
    if not settings.DEBUG:
        return HttpResponse("Forbidden: This page is only available in DEBUG mode".encode('utf-8'), status=403)
    
    headers = {}
    
    # Content Security Policy
    headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'"
    
    # HTTP Strict Transport Security
    headers['Strict-Transport-Security'] = "max-age=31536000; includeSubDomains"
    
    # X-Content-Type-Options
    headers['X-Content-Type-Options'] = "nosniff"
    
    # X-Frame-Options
    headers['X-Frame-Options'] = "SAMEORIGIN"
    
    # X-XSS-Protection
    headers['X-XSS-Protection'] = "1; mode=block"
    
    # Referrer-Policy
    headers['Referrer-Policy'] = "strict-origin-when-cross-origin"
    
    # Feature-Policy
    headers['Feature-Policy'] = "geolocation 'self'; microphone 'none'; camera 'none'"
    
    # Permissions-Policy (newer version of Feature-Policy)
    headers['Permissions-Policy'] = "geolocation=(self), microphone=(), camera=()"
    
    html_content = """
        <html>
        <head>
            <title>Security Headers Test</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; direction: rtl; }
                h1 { color: #333; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { padding: 10px; text-align: right; border: 1px solid #ddd; }
                th { background-color: #f5f5f5; }
                tr:nth-child(even) { background-color: #f9f9f9; }
                code { font-family: monospace; background-color: #f5f5f5; padding: 2px 4px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h1>تست هدرهای امنیتی</h1>
            <p>این صفحه برای آزمایش هدرهای امنیتی است. هدرهای زیر در پاسخ HTTP این صفحه گنجانده شده‌اند:</p>
            
            <table>
                <tr>
                    <th>هدر</th>
                    <th>مقدار</th>
                    <th>توضیحات</th>
                </tr>
                <tr>
                    <td>Content-Security-Policy</td>
                    <td><code>default-src 'self'; script-src 'self' 'unsafe-inline'</code></td>
                    <td>محدود کردن منابع مجاز برای بارگذاری محتوا</td>
                </tr>
                <tr>
                    <td>Strict-Transport-Security</td>
                    <td><code>max-age=31536000; includeSubDomains</code></td>
                    <td>اجبار استفاده از HTTPS</td>
                </tr>
                <tr>
                    <td>X-Content-Type-Options</td>
                    <td><code>nosniff</code></td>
                    <td>جلوگیری از MIME type sniffing</td>
                </tr>
                <tr>
                    <td>X-Frame-Options</td>
                    <td><code>SAMEORIGIN</code></td>
                    <td>محافظت از Clickjacking</td>
                </tr>
                <tr>
                    <td>X-XSS-Protection</td>
                    <td><code>1; mode=block</code></td>
                    <td>محافظت از حملات XSS</td>
                </tr>
                <tr>
                    <td>Referrer-Policy</td>
                    <td><code>strict-origin-when-cross-origin</code></td>
                    <td>کنترل اطلاعات Referrer</td>
                </tr>
                <tr>
                    <td>Feature-Policy</td>
                    <td><code>geolocation 'self'; microphone 'none'; camera 'none'</code></td>
                    <td>محدود کردن دسترسی به ویژگی‌های حساس</td>
                </tr>
                <tr>
                    <td>Permissions-Policy</td>
                    <td><code>geolocation=(self), microphone=(), camera=()</code></td>
                    <td>نسخه جدیدتر Feature-Policy</td>
                </tr>
            </table>
            
            <h2>تست CSP</h2>
            <p>این اسکریپت اجرا نخواهد شد، چون منبع آن با CSP مطابقت ندارد:</p>
            <pre><code>&lt;script src="https://example.com/malicious.js"&gt;&lt;/script&gt;</code></pre>
            <script src="https://example.com/malicious.js"></script>
            
            <h2>اطلاعات مرورگر</h2>
            <p>User-Agent شما: <code id="user-agent">?</code></p>
            
            <script>
                // این اسکریپت اجرا خواهد شد، چون با CSP مطابقت دارد
                document.getElementById('user-agent').textContent = navigator.userAgent;
            </script>
        </body>
        </html>
        """
    
    response = HttpResponse(html_content.encode('utf-8'))
    
    # افزودن همه هدرها به پاسخ
    for header, value in headers.items():
        response[header] = value
    
    return response

def security_error_handler(request, exception=None):
    """
    هندلر خطاهای امنیتی سفارشی برای صفحات 403، 404 و 500
    """
    status_code = getattr(exception, 'status_code', 403)
    
    if status_code == 404:
        message = "صفحه مورد نظر یافت نشد."
        error_code = "PAGE_NOT_FOUND"
    elif status_code == 403:
        message = "دسترسی به این صفحه مجاز نیست."
        error_code = "ACCESS_DENIED"
    elif status_code == 500:
        message = "خطای داخلی سرور رخ داده است."
        error_code = "SERVER_ERROR"
    else:
        message = "خطای امنیتی رخ داده است."
        error_code = f"SEC-{status_code}"
    
    # ثبت اطلاعات در لاگ امنیتی
    security_logger.warning(
        f"Security error: {error_code} - {message}",
        extra={
            'ip': _get_client_ip(request),
            'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
            'path': request.path
        }
    )
    
    # تشخیص درخواست API
    if ('application/json' in request.headers.get('Accept', '') or
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'):
        return JsonResponse({
            'error': True,
            'message': message,
            'error_code': error_code,
            'status': status_code
        }, status=status_code)
    
    # نمایش صفحه خطای امنیتی
    context = {
        'message': message,
        'status_code': status_code,
        'error_code': error_code,
        'show_details': settings.DEBUG,
        'security_tip': "سیستم مجهز به سامانه تشخیص و دفع حملات است. فعالیت‌های مشکوک ثبت و پیگیری می‌شوند."
    }
    
    return render(request, 'security/error.html', context, status=status_code)

def _get_client_ip(request):
    """دریافت IP واقعی کاربر با در نظر گرفتن پراکسی‌ها"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip