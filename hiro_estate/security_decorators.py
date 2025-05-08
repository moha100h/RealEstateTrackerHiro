"""
مجموعه دکوراتورها و ابزارهای امنیتی پیشرفته
برای محافظت از API ها و ویوهای وب
"""

import time
import functools
import hashlib
import hmac
import base64
import logging
import re
import ipaddress
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.conf import settings
from django.utils.crypto import constant_time_compare
from django.core.cache import cache
from django.utils.translation import gettext as _

# لاگ سیستم امنیتی
security_logger = logging.getLogger('security')

def secure_api(trusted_networks=None, required_permission=None, validate_request=True):
    """
    دکوراتور پیشرفته امنیتی برای API ها
    - اعتبارسنجی IP مبدأ
    - بررسی دسترسی‌های کاربر
    - اعتبارسنجی ساختاری درخواست
    - محدودیت نرخ درخواست (Rate Limiting)
    - بررسی امضای درخواست
    """
    if trusted_networks is None:
        trusted_networks = ['127.0.0.1/32', '::1/128']  # فقط localhost
    
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # ۱. اعتبارسنجی IP
            client_ip = _get_client_ip(request)
            if not _is_ip_allowed(client_ip, trusted_networks):
                security_logger.warning(
                    f"API access blocked: Unauthorized IP address: {client_ip}", 
                    extra={'ip': client_ip, 'user': 'anonymous'}
                )
                
                return _security_error_response(
                    request, 
                    status_code=403, 
                    message="دسترسی به این API از IP شما مجاز نیست.",
                    error_code="IP_NOT_ALLOWED"
                )
            
            # ۲. بررسی دسترسی کاربر
            if required_permission and hasattr(request, 'user'):
                if not request.user.is_authenticated:
                    return _security_error_response(
                        request, 
                        status_code=401, 
                        message="برای دسترسی به این API باید وارد سیستم شوید.",
                        error_code="AUTH_REQUIRED"
                    )
                
                if not request.user.has_perm(required_permission):
                    security_logger.warning(
                        f"API permission denied: User {request.user.username} lacks {required_permission}", 
                        extra={'ip': client_ip, 'user': request.user.username}
                    )
                    
                    return _security_error_response(
                        request, 
                        status_code=403, 
                        message="شما دسترسی لازم برای استفاده از این API را ندارید.",
                        error_code="PERMISSION_DENIED"
                    )
            
            # ۳. اعتبارسنجی امضای درخواست (برای API های خارجی)
            api_key = request.headers.get('X-API-Key')
            if api_key and hasattr(settings, 'API_KEYS'):
                signature = request.headers.get('X-API-Signature')
                timestamp = request.headers.get('X-API-Timestamp')
                
                # بررسی وجود همه هدرهای لازم
                if not all([signature, timestamp]):
                    return _security_error_response(
                        request, 
                        status_code=401, 
                        message="هدرهای امنیتی API ناقص است.",
                        error_code="INCOMPLETE_AUTH_HEADERS"
                    )
                
                # بررسی اعتبار زمانی
                try:
                    req_time = float(timestamp)
                    current_time = time.time()
                    
                    # درخواست نباید بیش از ۵ دقیقه قدیمی باشد
                    if abs(current_time - req_time) > 300:
                        return _security_error_response(
                            request, 
                            status_code=401, 
                            message="درخواست API منقضی شده است.",
                            error_code="REQUEST_EXPIRED"
                        )
                except ValueError:
                    return _security_error_response(
                        request, 
                        status_code=401, 
                        message="فرمت timestamp نامعتبر است.",
                        error_code="INVALID_TIMESTAMP"
                    )
                
                # اعتبارسنجی امضا
                if api_key not in settings.API_KEYS:
                    return _security_error_response(
                        request, 
                        status_code=401, 
                        message="کلید API نامعتبر است.",
                        error_code="INVALID_API_KEY"
                    )
                
                api_secret = settings.API_KEYS[api_key]
                expected_signature = _generate_request_signature(request, timestamp, api_secret)
                
                if not constant_time_compare(signature, expected_signature):
                    security_logger.warning(
                        f"API signature verification failed for API key: {api_key}", 
                        extra={'ip': client_ip, 'user': 'api'}
                    )
                    
                    return _security_error_response(
                        request, 
                        status_code=401, 
                        message="امضای API نامعتبر است.",
                        error_code="INVALID_SIGNATURE"
                    )
            
            # ۴. محدودیت نرخ درخواست (Rate Limiting)
            rate_key = f"api_rate:{client_ip}"
            current_rate = cache.get(rate_key, 0)
            
            # محدودیت پیش‌فرض: ۱۰۰ درخواست در دقیقه
            rate_limit = getattr(settings, 'API_RATE_LIMIT', 100)
            
            if current_rate >= rate_limit:
                security_logger.warning(
                    f"API rate limit exceeded: {client_ip} - {current_rate}/{rate_limit} requests", 
                    extra={'ip': client_ip, 'user': 'api' if api_key else 'anonymous'}
                )
                
                return _security_error_response(
                    request, 
                    status_code=429, 
                    message="تعداد درخواست‌های شما بیش از حد مجاز است. لطفاً کمی صبر کنید.",
                    error_code="RATE_LIMIT_EXCEEDED"
                )
            
            # افزایش شمارنده درخواست
            cache.set(rate_key, current_rate + 1, 60)  # منقضی شدن بعد از ۶۰ ثانیه
            
            # اجرای ویو اصلی
            try:
                return view_func(request, *args, **kwargs)
            except Exception as e:
                # ثبت خطا در لاگ امنیتی
                security_logger.error(
                    f"API error: {str(e)}", 
                    extra={'ip': client_ip, 'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'},
                    exc_info=True
                )
                
                # بازگرداندن پاسخ خطای امنیتی
                return _security_error_response(
                    request, 
                    status_code=500, 
                    message="خطایی در پردازش درخواست رخ داده است.",
                    error_code="API_ERROR"
                )
        
        return wrapper
    
    return decorator

def csrf_exempt_with_validation(view_func):
    """
    نسخه امن‌تر CSRF exempt با اعتبارسنجی‌های امنیتی اضافی
    بررسی Origin و Referer
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # بررسی Origin و Referer برای جلوگیری از CSRF
        origin = request.headers.get('Origin')
        referer = request.headers.get('Referer')
        
        host = request.get_host()
        
        trusted_origins = getattr(settings, 'CSRF_TRUSTED_ORIGINS', [])
        
        # افزودن دامنه خود سایت به دامنه‌های مجاز
        if host:
            protocol = 'https' if request.is_secure() else 'http'
            self_origin = f"{protocol}://{host}"
            trusted_origins.append(self_origin)
        
        # بررسی Origin
        if origin and not any(origin.startswith(trusted) for trusted in trusted_origins):
            security_logger.warning(
                f"CSRF protection: Invalid Origin header: {origin}", 
                extra={'ip': _get_client_ip(request), 'user': 'anonymous'}
            )
            
            return _security_error_response(
                request, 
                status_code=403, 
                message="درخواست از دامنه غیرمجاز دریافت شده است.",
                error_code="INVALID_ORIGIN"
            )
        
        # بررسی Referer
        if referer and not any(referer.startswith(trusted) for trusted in trusted_origins):
            security_logger.warning(
                f"CSRF protection: Invalid Referer header: {referer}", 
                extra={'ip': _get_client_ip(request), 'user': 'anonymous'}
            )
            
            return _security_error_response(
                request, 
                status_code=403, 
                message="ارجاع‌دهنده نامعتبر است.",
                error_code="INVALID_REFERER"
            )
        
        # اجرای ویو اصلی با دور زدن محافظت CSRF
        from django.views.decorators.csrf import csrf_exempt
        return csrf_exempt(view_func)(request, *args, **kwargs)
    
    return wrapper

def detect_injection_attempts(view_func):
    """
    دکوراتور تشخیص حملات تزریق (SQL, XSS, Command Injection)
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # الگوهای حملات تزریق معروف
        sql_patterns = [
            r'(\bSELECT\b.*\bFROM\b|\bUNION\b.*\bSELECT\b|\bINSERT\b.*\bINTO\b|\bUPDATE\b.*\bSET\b|\bDELETE\b.*\bFROM\b|\bDROP\b.*\bTABLE\b)',
            r"('[0-9]+=[0-9]+--| OR |' ?OR ?1=1|' ?OR ?'1'='1)",
            r'(--;|/\*|\*/)'
        ]
        
        xss_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'onload=|onerror=|onmouseover=|onfocus=|onclick=',
            r'document\.cookie|document\.location|document\.write',
            r'eval\s*\(|setTimeout\s*\(|setInterval\s*\('
        ]
        
        cmd_patterns = [
            r';.*?[|&]',
            r'`.*?`',
            r'\$\(.*?\)',
            r'>\s*[a-zA-Z0-9_.-/]+',
            r'\|\s*[a-zA-Z0-9_.-/]+'
        ]
        
        # ترکیب همه الگوها
        all_patterns = sql_patterns + xss_patterns + cmd_patterns
        
        # بررسی پارامترهای URL
        for param, value in request.GET.items():
            for pattern in all_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    security_logger.warning(
                        f"Injection attempt detected in GET param '{param}': {value[:50]}", 
                        extra={'ip': _get_client_ip(request), 'user': 'anonymous'}
                    )
                    
                    return _security_error_response(
                        request, 
                        status_code=400, 
                        message="الگوی مشکوک در پارامترهای درخواست تشخیص داده شد.",
                        error_code="INJECTION_ATTEMPT"
                    )
        
        # بررسی داده‌های POST
        if request.method == 'POST':
            for param, value in request.POST.items():
                if isinstance(value, str):
                    for pattern in all_patterns:
                        if re.search(pattern, value, re.IGNORECASE):
                            security_logger.warning(
                                f"Injection attempt detected in POST param '{param}': {value[:50]}", 
                                extra={'ip': _get_client_ip(request), 'user': 'anonymous'}
                            )
                            
                            return _security_error_response(
                                request, 
                                status_code=400, 
                                message="الگوی مشکوک در داده‌های ارسالی تشخیص داده شد.",
                                error_code="INJECTION_ATTEMPT"
                            )
        
        # بررسی هدرهای درخواست
        sensitive_headers = ['User-Agent', 'Referer', 'Cookie']
        for header in sensitive_headers:
            value = request.headers.get(header, '')
            if value:
                for pattern in all_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        security_logger.warning(
                            f"Injection attempt detected in header '{header}': {value[:50]}", 
                            extra={'ip': _get_client_ip(request), 'user': 'anonymous'}
                        )
                        
                        return _security_error_response(
                            request, 
                            status_code=400, 
                            message="الگوی مشکوک در هدرهای درخواست تشخیص داده شد.",
                            error_code="INJECTION_ATTEMPT"
                        )
        
        # اجرای ویو اصلی
        return view_func(request, *args, **kwargs)
    
    return wrapper

def require_https(view_func):
    """
    دکوراتور اجبار استفاده از HTTPS
    با بررسی هدرهای پراکسی معتبر
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # بررسی HTTPS بودن درخواست با در نظر گرفتن پراکسی‌ها
        is_secure = request.is_secure()
        forwarded_proto = request.META.get('HTTP_X_FORWARDED_PROTO')
        
        if forwarded_proto == 'https':
            is_secure = True
        
        if not is_secure and not settings.DEBUG:
            security_logger.warning(
                f"Insecure HTTP request blocked", 
                extra={'ip': _get_client_ip(request), 'user': 'anonymous'}
            )
            
            # ریدایرکت به نسخه HTTPS
            from django.http import HttpResponseRedirect
            url = request.build_absolute_uri(request.path)
            secure_url = url.replace('http://', 'https://', 1)
            
            return HttpResponseRedirect(secure_url)
        
        # اجرای ویو اصلی
        return view_func(request, *args, **kwargs)
    
    return wrapper

def _get_client_ip(request):
    """دریافت IP واقعی کاربر با در نظر گرفتن پراکسی‌ها"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip

def _is_ip_allowed(ip, allowed_networks):
    """بررسی دسترسی IP بر اساس لیست شبکه‌های مجاز"""
    # تبدیل IP به آبجکت ipaddress
    try:
        client_ip = ipaddress.ip_address(ip)
    except ValueError:
        return False
    
    # بررسی تطابق با شبکه‌های مجاز
    for network_str in allowed_networks:
        try:
            network = ipaddress.ip_network(network_str)
            if client_ip in network:
                return True
        except ValueError:
            continue
    
    return False

def _generate_request_signature(request, timestamp, secret_key):
    """تولید امضای درخواست برای احراز هویت API"""
    # ساخت رشته برای امضا
    method = request.method.upper()
    path = request.path
    query_string = request.META.get('QUERY_STRING', '')
    
    # برای درخواست‌های POST، افزودن داده‌های body
    body = ''
    if method == 'POST' and hasattr(request, 'body'):
        body = request.body.decode('utf-8', errors='ignore')
    
    # ساخت رشته نهایی برای امضا
    string_to_sign = f"{method}\n{path}\n{query_string}\n{timestamp}\n{body}"
    
    # تولید امضا با HMAC
    hmac_digest = hmac.new(
        secret_key.encode('utf-8'),
        string_to_sign.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    # تبدیل به base64 برای ارسال در هدر
    return base64.b64encode(hmac_digest).decode('utf-8')

def _security_error_response(request, status_code=403, message=None, error_code=None, detail=None):
    """ایجاد پاسخ خطای امنیتی مناسب"""
    # پیام‌های پیش‌فرض
    if message is None:
        message = "دسترسی به این منبع به دلایل امنیتی مسدود شده است."
    
    if error_code is None:
        error_code = f"SEC-{status_code}"
    
    # پاسخ متفاوت برای درخواست‌های API و وب
    is_api_request = (
        'application/json' in request.headers.get('Accept', '') or
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    )
    
    if is_api_request:
        return JsonResponse({
            'error': True,
            'message': message,
            'error_code': error_code,
            'status': status_code
        }, status=status_code)
    else:
        # نمایش صفحه خطای امنیتی
        return render(request, 'security/error.html', {
            'message': message,
            'status_code': status_code,
            'error_code': error_code,
            'detail': detail,
            'show_details': settings.DEBUG,
            'security_tip': "سیستم مجهز به سامانه تشخیص و دفع حملات است. فعالیت‌های مشکوک ثبت و پیگیری می‌شوند."
        }, status=status_code)

# استفاده از دکوراتورها:
# @secure_api(trusted_networks=['10.0.0.0/8', '192.168.0.0/16'])
# @detect_injection_attempts
# @require_https
# def my_api_view(request):
#     # پردازش درخواست
#     return JsonResponse({'status': 'success'})