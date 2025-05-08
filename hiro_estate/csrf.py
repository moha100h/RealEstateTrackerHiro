"""
ماژول محافظت پیشرفته در برابر حملات CSRF
تقویت امنیت سیستم با محافظت‌های چندلایه
"""

import time
import hmac
import hashlib
import base64
import logging
import re
import os
from django.middleware.csrf import get_token as django_get_token
from django.utils.crypto import constant_time_compare
from django.http import HttpResponseForbidden
from django.conf import settings
from django.utils.cache import patch_vary_headers
from django.core.cache import cache
from django.http import JsonResponse

# لاگر امنیتی
security_logger = logging.getLogger('security')

def get_enhanced_csrf_token(request):
    """
    ایجاد توکن CSRF پیشرفته با اطلاعات اضافی برای امنیت بیشتر
    """
    # دریافت توکن CSRF اصلی
    csrf_token = django_get_token(request)
    
    # افزودن لایه امنیتی اضافی
    if hasattr(request, 'user') and request.user.is_authenticated:
        # اضافه کردن اطلاعات نشست و کاربر
        user_id = str(request.user.id)
        session_key = request.session.session_key or ''
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:100]  # محدود کردن طول
        
        # ترکیب اطلاعات و ایجاد یک توکن پیشرفته
        data = f"{csrf_token}:{user_id}:{session_key}:{_hash_string(user_agent)}"
        
        # رمزنگاری با کلید مخفی سایت
        enhanced_token = _encrypt_token(data, settings.SECRET_KEY)
        return enhanced_token
    
    # برای کاربران ناشناس، استفاده از توکن استاندارد
    return csrf_token

def verify_enhanced_csrf_token(request, token):
    """
    تأیید اعتبار توکن CSRF پیشرفته
    """
    # بررسی توکن‌های خالی
    if not token or token == 'None':
        return False
    
    # برای کاربران احراز هویت شده، توکن پیشرفته را بررسی می‌کنیم
    if hasattr(request, 'user') and request.user.is_authenticated:
        try:
            # رمزگشایی توکن
            decrypted = _decrypt_token(token, settings.SECRET_KEY)
            
            # جداسازی اجزا
            parts = decrypted.split(':')
            if len(parts) != 4:
                return False
            
            original_token, user_id, session_key, user_agent_hash = parts
            
            # بررسی تطابق اطلاعات
            current_user_id = str(request.user.id)
            current_session_key = request.session.session_key or ''
            current_user_agent = request.META.get('HTTP_USER_AGENT', '')[:100]
            current_user_agent_hash = _hash_string(current_user_agent)
            
            # بررسی توکن CSRF اصلی
            csrf_token_valid = constant_time_compare(original_token, django_get_token(request))
            
            # بررسی تطابق کاربر و نشست
            user_valid = constant_time_compare(user_id, current_user_id)
            session_valid = constant_time_compare(session_key, current_session_key)
            agent_valid = constant_time_compare(user_agent_hash, current_user_agent_hash)
            
            # بررسی مجموع اعتبارسنجی‌ها
            if csrf_token_valid and user_valid and (session_valid or agent_valid):
                return True
            
            # ثبت تلاش ناموفق تأیید توکن
            security_logger.warning(
                "Enhanced CSRF token validation failed",
                extra={
                    'ip': _get_client_ip(request),
                    'user': request.user.username,
                    'csrf_valid': csrf_token_valid,
                    'user_valid': user_valid,
                    'session_valid': session_valid,
                    'agent_valid': agent_valid
                }
            )
            
            return False
            
        except Exception as e:
            security_logger.error(f"Error verifying enhanced CSRF token: {str(e)}")
            return False
    
    # برای کاربران ناشناس، بررسی استاندارد انجام می‌شود
    return constant_time_compare(token, django_get_token(request))

def enhanced_csrf_failure(request, reason=""):
    """
    هندلر پیشرفته خطای CSRF
    """
    # ثبت تلاش CSRF در لاگ امنیتی
    client_ip = _get_client_ip(request)
    user = request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
    
    security_logger.warning(
        f"CSRF verification failed: {reason}",
        extra={
            'ip': client_ip,
            'user': user,
            'path': request.path,
            'method': request.method,
            'referrer': request.META.get('HTTP_REFERER', 'unknown')
        }
    )
    
    # بررسی حمله هماهنگ CSRF
    csrf_key = f"csrf_failures:{client_ip}"
    current_failures = cache.get(csrf_key, 0) + 1
    cache.set(csrf_key, current_failures, 3600)  # منقضی شدن بعد از یک ساعت
    
    # اگر تعداد خطاهای CSRF از حد مجاز بیشتر باشد، به سیستم تشخیص حمله هشدار می‌دهیم
    if current_failures > 5:
        security_logger.error(
            f"Multiple CSRF failures from IP: {client_ip}. Possible attack.",
            extra={
                'ip': client_ip,
                'user': user,
                'count': current_failures
            }
        )
        
        # محدودیت IP در سیستم واقعی
        # cache.set(f"block_ip:{client_ip}", True, 7200)  # مسدود کردن برای 2 ساعت
    
    # پاسخ خطا برای درخواست‌های AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'CSRF verification failed. Please refresh the page and try again.',
            'code': 'csrf_failure'
        }, status=403)
    
    # استفاده از صفحه خطای سفارشی
    from django.shortcuts import render
    return render(request, 'security/error.html', {
        'message': 'توکن امنیتی CSRF نامعتبر است. لطفاً صفحه را بارگذاری مجدد کنید.',
        'status_code': 403,
        'error_code': 'CSRF_FAILURE',
        'security_tip': 'این خطا ممکن است به دلیل منقضی شدن نشست یا تلاش برای حمله فیشینگ رخ داده باشد.'
    }, status=403)

class EnhancedCSRFMiddleware:
    """
    میدل‌ویر پیشرفته CSRF با امنیت چندلایه
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.csrf_exempt_paths = getattr(settings, 'CSRF_EXEMPT_PATHS', [])
        
    def __call__(self, request):
        # اضافه کردن توکن پیشرفته به درخواست
        request.enhanced_csrf_token = get_enhanced_csrf_token(request)
        
        # پردازش درخواست
        response = self.get_response(request)
        
        # اضافه کردن هدر متنوع برای کش‌های پراکسی
        patch_vary_headers(response, ('Cookie',))
        
        return response
    
    def process_view(self, request, callback, callback_args, callback_kwargs):
        # بررسی معافیت‌های CSRF
        path = request.path_info.lstrip('/')
        
        # مسیرهای معاف از بررسی CSRF
        if any(re.match(exempt, path) for exempt in self.csrf_exempt_paths):
            return None
        
        # معافیت با دکوراتور csrf_exempt
        if getattr(callback, 'csrf_exempt', False):
            return None
        
        # فقط درخواست‌های POST/PUT/DELETE نیاز به بررسی دارند
        if request.method not in ('POST', 'PUT', 'DELETE'):
            return None
        
        # تأیید اعتبار توکن CSRF
        csrf_token = request.META.get('HTTP_X_CSRFTOKEN') or request.POST.get('csrfmiddlewaretoken')
        if not verify_enhanced_csrf_token(request, csrf_token):
            return enhanced_csrf_failure(request)
        
        return None

def _encrypt_token(data, key):
    """رمزنگاری توکن با کلید مخفی"""
    key_bytes = hashlib.sha256(key.encode()).digest()
    
    # ایجاد HMAC برای تأیید اصالت
    signature = hmac.new(key_bytes, data.encode(), hashlib.sha256).digest()
    
    # ترکیب داده و امضا
    combined = data.encode() + signature
    
    # تبدیل به base64 برای استفاده در URL
    return base64.urlsafe_b64encode(combined).decode()

def _decrypt_token(token, key):
    """رمزگشایی توکن با کلید مخفی"""
    key_bytes = hashlib.sha256(key.encode()).digest()
    
    # رمزگشایی از base64
    try:
        decoded = base64.urlsafe_b64decode(token)
    except Exception:
        return ""
    
    # جداسازی داده و امضا
    data = decoded[:-32]  # ۳۲ بایت آخر امضا هستند
    signature = decoded[-32:]
    
    # بررسی اصالت با HMAC
    expected_sig = hmac.new(key_bytes, data, hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected_sig):
        return ""
    
    # بازگرداندن داده اصلی
    return data.decode()

def _hash_string(value):
    """ساخت هش امن از رشته"""
    return hashlib.sha256(value.encode()).hexdigest()

def _get_client_ip(request):
    """دریافت IP واقعی کاربر"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip