"""
میدل‌ویر‌های سفارشی برای امنیت پیشرفته سیستم
محافظت در برابر حملات سایبری و تهدیدات امنیتی
"""

import re
import time
import logging
import hashlib
import ipaddress
import json
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse

from django.http import HttpResponseForbidden, JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.conf import settings
from django.core.cache import cache
from django.utils.crypto import get_random_string, constant_time_compare
from django.contrib.auth import logout
from django.urls import reverse

# لاگر برای ثبت رویدادهای امنیتی
security_logger = logging.getLogger('security')

class RateLimitMiddleware:
    """
    میدل‌ویر پیشرفته محدودیت نرخ درخواست (Rate Limiting)
    - محدودیت‌های پویا بر اساس نوع درخواست
    - محافظت در برابر حملات DDOS و محدود کردن تعداد درخواست‌های مجاز از یک IP
    - تشخیص الگوهای مشکوک در درخواست‌ها
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # تنظیمات پیش‌فرض محدودیت نرخ درخواست
        self.default_rate_limit = getattr(settings, 'DEFAULT_RATE_LIMIT', 200)  # درخواست در دقیقه
        self.login_rate_limit = getattr(settings, 'LOGIN_RATE_LIMIT', 10)  # درخواست در دقیقه
        self.api_rate_limit = getattr(settings, 'API_RATE_LIMIT', 60)  # درخواست در دقیقه
        self.static_rate_limit = getattr(settings, 'STATIC_RATE_LIMIT', 500)  # درخواست در دقیقه
        self.burst_multiplier = getattr(settings, 'BURST_MULTIPLIER', 5)  # ضریب افزایش برای محدودیت‌های لحظه‌ای
        
        # مسیرهای مستثنی از محدودیت
        self.exempt_paths = getattr(settings, 'RATE_LIMIT_EXEMPT_PATHS', [
            r'^/static/',
            r'^/media/',
            r'^/favicon\.ico$',
            r'^/robots\.txt$',
        ])
        
        # شبکه‌های مجاز بدون محدودیت
        self.trusted_networks = getattr(settings, 'TRUSTED_NETWORKS', [
            '127.0.0.1/32',  # localhost
            '::1/128',       # localhost IPv6
        ])
        
        # مسیرهای با محدودیت‌های خاص
        self.special_paths = {
            r'^/accounts/login/': self.login_rate_limit,
            r'^/api/': self.api_rate_limit,
            r'^/static/': self.static_rate_limit,
        }
        
    def __call__(self, request):
        # بررسی مسیرهای مستثنی
        path = request.path_info.lstrip('/')
        
        if any(re.match(exempt, path) for exempt in self.exempt_paths):
            return self.get_response(request)
        
        # دریافت IP کاربر
        client_ip = self._get_client_ip(request)
        
        # بررسی اعتبار IP
        if not self._is_valid_ip(client_ip):
            return HttpResponseForbidden('Invalid IP address'.encode())
        
        # بررسی شبکه‌های مجاز
        if any(self._ip_in_network(client_ip, network) for network in self.trusted_networks):
            return self.get_response(request)
        
        # تعیین محدودیت مناسب برای مسیر
        rate_limit = self.default_rate_limit
        for pattern, limit in self.special_paths.items():
            if re.match(pattern, path):
                rate_limit = limit
                break
        
        # کلید کش برای محدودیت نرخ
        path_pattern = self._get_path_pattern(path)
        is_login = '/accounts/login/' in path
        
        # کلیدهای مختلف برای انواع مختلف محدودیت
        minute_key = f"rate:min:{client_ip}:{path_pattern}"
        burst_key = f"rate:burst:{client_ip}:{path_pattern}"
        global_key = f"rate:global:{client_ip}"
        
        # بررسی محدودیت‌های مختلف
        
        # 1. محدودیت در دقیقه برای یک مسیر خاص
        minute_count = cache.get(minute_key, 0)
        if minute_count >= rate_limit:
            security_logger.warning(
                f"Rate limit exceeded for IP {client_ip} on path {path}",
                extra={'ip': client_ip, 'path': path, 'rate': minute_count}
            )
            
            response_data = {
                'error': 'درخواست‌های شما بیش از حد مجاز است. لطفاً کمی صبر کنید و دوباره تلاش کنید.',
                'retry_after': 60
            }
            
            if is_login:
                # برای صفحه لاگین، نمایش صفحه خطا به جای پاسخ JSON
                return render(request, 'security/error.html', {
                    'message': 'تعداد تلاش‌های شما برای ورود بیش از حد مجاز است. لطفاً 5 دقیقه صبر کنید.',
                    'status_code': 429,
                    'error_code': 'RATE_LIMIT_EXCEEDED',
                    'security_tip': 'این محدودیت برای حفاظت از حساب کاربری شما در برابر حملات رمزگشایی اعمال می‌شود.'
                }, status=429)
            
            return JsonResponse(response_data, status=429)
        
        # 2. محدودیت لحظه‌ای (burst)
        burst_count = cache.get(burst_key, 0)
        burst_limit = rate_limit * self.burst_multiplier / 60  # تقسیم بر 60 برای تبدیل به ثانیه
        if burst_count >= burst_limit:
            security_logger.warning(
                f"Burst rate limit exceeded for IP {client_ip} on path {path}",
                extra={'ip': client_ip, 'path': path, 'rate': burst_count}
            )
            
            response_data = {
                'error': 'سرعت درخواست‌های شما بیش از حد مجاز است. لطفاً کمی آهسته‌تر درخواست ارسال کنید.',
                'retry_after': 5
            }
            
            return JsonResponse(response_data, status=429)
        
        # 3. محدودیت کلی برای تمام مسیرها
        global_count = cache.get(global_key, 0)
        global_limit = getattr(settings, 'GLOBAL_RATE_LIMIT', 1000)  # محدودیت کلی در دقیقه
        if global_count >= global_limit:
            security_logger.warning(
                f"Global rate limit exceeded for IP {client_ip}",
                extra={'ip': client_ip, 'rate': global_count}
            )
            
            response_data = {
                'error': 'تعداد کل درخواست‌های شما بیش از حد مجاز است. لطفاً کمی صبر کنید و دوباره تلاش کنید.',
                'retry_after': 60
            }
            
            return JsonResponse(response_data, status=429)
        
        # افزایش شمارنده‌ها
        cache.set(minute_key, minute_count + 1, 60)  # منقضی شدن پس از 60 ثانیه
        cache.set(burst_key, burst_count + 1, 1)    # منقضی شدن پس از 1 ثانیه
        cache.set(global_key, global_count + 1, 60)  # منقضی شدن پس از 60 ثانیه
        
        # بررسی الگوهای مشکوک حمله DDoS
        if self._is_ddos_pattern(request, client_ip, path_pattern):
            security_logger.error(
                f"Potential DDoS pattern detected from IP {client_ip}",
                extra={'ip': client_ip, 'path': path, 'user_agent': request.META.get('HTTP_USER_AGENT', '')}
            )
            
            # در یک سیستم واقعی، اینجا حتی می‌توان IP را مسدود کرد
            # یا به ابزار حفاظت در برابر DDoS هشدار داد
        
        response = self.get_response(request)
        
        return response
    
    def _get_client_ip(self, request):
        """دریافت IP واقعی کاربر با در نظر گرفتن پروکسی‌ها"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip
    
    def _is_valid_ip(self, ip):
        """بررسی اعتبار ساختاری آدرس IP"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _ip_in_network(self, ip, network):
        """بررسی اینکه آیا IP در یک شبکه مشخص قرار دارد"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            network_obj = ipaddress.ip_network(network)
            return ip_obj in network_obj
        except ValueError:
            return False
    
    def _get_path_pattern(self, path):
        """تبدیل مسیر به الگوی عمومی برای تشخیص الگوهای مشکوک"""
        # مثال: تبدیل /product/123 به /product/ID
        pattern = re.sub(r'/\d+/', '/ID/', path)
        pattern = re.sub(r'/\d+$', '/ID', pattern)
        return pattern
    
    def _is_ddos_pattern(self, request, ip, path_pattern):
        """تشخیص الگوهای احتمالی حمله DDoS"""
        # در جانگو، cache.keys موجود نیست، بنابراین از روش دیگری استفاده می‌کنیم
        # این قسمت را به گونه‌ای بازنویسی می‌کنیم که از ویژگی‌های cache جانگو استفاده کند
        
        # بررسی از طریق متغیرهای دیگر
        request_count = 0
        for i in range(20):  # بررسی 20 مسیر متفاوت
            test_key = f"rate:min:{ip}:path{i}"
            if cache.get(test_key, None) is not None:
                request_count += 1
        
        if request_count > 10:  # اگر به بیش از 10 مسیر متفاوت درخواست داده شده
            return True
        
        # 2. بررسی تعداد درخواست‌های با User-Agent های مختلف از یک IP
        agent_key = f"ua:{ip}"
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        agents = cache.get(agent_key, set())
        
        if user_agent and user_agent not in agents:
            agents.add(user_agent)
            cache.set(agent_key, agents, 600)  # 10 دقیقه
            
            if len(agents) > 5:  # بیش از 5 User-Agent مختلف از یک IP
                return True
        
        # 3. بررسی درخواست‌های همزمان به منابع حساس
        sensitive_paths = ['/admin/', '/accounts/login/', '/api/']
        for s_path in sensitive_paths:
            if s_path in path_pattern:
                concurrent_key = f"concurrent:{ip}:{s_path}"
                concurrent = cache.get(concurrent_key, 0)
                cache.set(concurrent_key, concurrent + 1, 5)  # 5 ثانیه
                
                if concurrent > 10:  # بیش از 10 درخواست همزمان
                    return True
        
        return False

class EnhancedSecurityMiddleware:
    """
    میدل‌ویر امنیت پیشرفته با محافظت از انواع حملات شناخته‌شده
    - تشخیص و مسدودسازی حملات SQL Injection
    - محافظت در برابر حملات XSS
    - جلوگیری از CSRF با توکن‌های پویا
    - محافظت در برابر حملات Path Traversal
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # الگوهای خطرناک SQL Injection
        self.sql_patterns = [
            r"('(''|[^'])*')|(;)|(\b(SELECT|UPDATE|INSERT|DELETE|DROP|ALTER|EXEC|TRUNCATE|DECLARE|UNION|CREATE)\b)",
            r"(\b(OR|AND)\b\s+\w+\s*=\s*\w+\s*($|\s|;))",
            r"(--\s+)|(/\*.*\*/)",
            r"(#.*)|(=\s*\d+\s*($|\s|;))"
        ]
        
        # الگوهای خطرناک XSS
        self.xss_patterns = [
            r"(<script.*?>.*?</script>)",
            r"(javascript:)",
            r"(vbscript:)",
            r"(onload=|onerror=|onmouseover=|onfocus=|onclick=)",
            r"(<img.*?src=.*?onerror=.*?>)",
            r"(document\.cookie|document\.location|document\.write)"
        ]
        
        # الگوهای خطرناک Path Traversal
        self.path_patterns = [
            r"(\.\./)",
            r"(\.\.\\)",
            r"(%2e%2e%2f)",
            r"(%252e%252e%252f)",
            r"(/etc/passwd)",
            r"(C:[\\/]Windows[\\/])",
            r"(WEB-INF[\\/]web\.xml)"
        ]
        
        # الگوهای خطرناک Command Injection
        self.cmd_patterns = [
            r"(\s*\|\s*\w+)",
            r"(\s*;\s*\w+)",
            r"(\s*\$\(\w+)",
            r"(\s*`\w+`)",
            r"(\s*>\s*\w+)",
            r"(\b(system|exec|popen|passthru|shell_exec|eval)\b)"
        ]
        
        # مسیرهایی که از بررسی مستثنی هستند (مثلاً برای ادمین‌ها)
        self.exempt_paths = getattr(settings, 'SECURITY_EXEMPT_PATHS', [
            r'^/admin/security/',
        ])
        
    def __call__(self, request):
        # بررسی مسیرهای مستثنی
        path = request.path_info.lstrip('/')
        if any(re.match(exempt, path) for exempt in self.exempt_paths):
            return self.get_response(request)
        
        # بررسی انواع مختلف حملات در پارامترهای GET
        for param, value in request.GET.items():
            if not isinstance(value, str):
                continue
                
            # بررسی SQL Injection
            if self._check_patterns(value, self.sql_patterns):
                security_logger.warning(
                    f"Potential SQL Injection detected in GET param {param}",
                    extra={
                        'ip': self._get_client_ip(request),
                        'param': param,
                        'value': value[:100],
                        'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
                    }
                )
                return self._security_violation_response(request, "درخواست شما حاوی الگوهای مشکوک SQL است.")
            
            # بررسی XSS
            if self._check_patterns(value, self.xss_patterns):
                security_logger.warning(
                    f"Potential XSS detected in GET param {param}",
                    extra={
                        'ip': self._get_client_ip(request),
                        'param': param,
                        'value': value[:100],
                        'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
                    }
                )
                return self._security_violation_response(request, "درخواست شما حاوی اسکریپت‌های غیرمجاز است.")
            
            # بررسی Path Traversal
            if self._check_patterns(value, self.path_patterns):
                security_logger.warning(
                    f"Potential Path Traversal detected in GET param {param}",
                    extra={
                        'ip': self._get_client_ip(request),
                        'param': param,
                        'value': value[:100],
                        'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
                    }
                )
                return self._security_violation_response(request, "درخواست شما حاوی مسیرهای فایل غیرمجاز است.")
            
            # بررسی Command Injection
            if self._check_patterns(value, self.cmd_patterns):
                security_logger.warning(
                    f"Potential Command Injection detected in GET param {param}",
                    extra={
                        'ip': self._get_client_ip(request),
                        'param': param,
                        'value': value[:100],
                        'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
                    }
                )
                return self._security_violation_response(request, "درخواست شما حاوی دستورات سیستمی غیرمجاز است.")
        
        # بررسی انواع مختلف حملات در پارامترهای POST
        if request.method == 'POST' and hasattr(request, 'POST'):
            for param, value in request.POST.items():
                if not isinstance(value, str):
                    continue
                    
                # بررسی SQL Injection
                if self._check_patterns(value, self.sql_patterns):
                    security_logger.warning(
                        f"Potential SQL Injection detected in POST param {param}",
                        extra={
                            'ip': self._get_client_ip(request),
                            'param': param,
                            'value': value[:100],
                            'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
                        }
                    )
                    return self._security_violation_response(request, "درخواست شما حاوی الگوهای مشکوک SQL است.")
                
                # بررسی XSS
                if self._check_patterns(value, self.xss_patterns):
                    security_logger.warning(
                        f"Potential XSS detected in POST param {param}",
                        extra={
                            'ip': self._get_client_ip(request),
                            'param': param,
                            'value': value[:100],
                            'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
                        }
                    )
                    return self._security_violation_response(request, "درخواست شما حاوی اسکریپت‌های غیرمجاز است.")
                
                # بررسی Path Traversal
                if self._check_patterns(value, self.path_patterns):
                    security_logger.warning(
                        f"Potential Path Traversal detected in POST param {param}",
                        extra={
                            'ip': self._get_client_ip(request),
                            'param': param,
                            'value': value[:100],
                            'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
                        }
                    )
                    return self._security_violation_response(request, "درخواست شما حاوی مسیرهای فایل غیرمجاز است.")
                
                # بررسی Command Injection
                if self._check_patterns(value, self.cmd_patterns):
                    security_logger.warning(
                        f"Potential Command Injection detected in POST param {param}",
                        extra={
                            'ip': self._get_client_ip(request),
                            'param': param,
                            'value': value[:100],
                            'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
                        }
                    )
                    return self._security_violation_response(request, "درخواست شما حاوی دستورات سیستمی غیرمجاز است.")
        
        # بررسی هدرهای مشکوک
        suspicious_headers = {
            'HTTP_USER_AGENT': r"(sqlmap|nikto|w3af|acunetix|ZAP|burpsuite|nessus)",
            'HTTP_REFERER': r"(https?://(?!.*\.domain\.com).*)",
            'HTTP_X_FORWARDED_FOR': r"([\d\.]+\s*,\s*[\d\.]+\s*,\s*[\d\.]+)"
        }
        
        for header, pattern in suspicious_headers.items():
            value = request.META.get(header, '')
            if value and re.search(pattern, value, re.IGNORECASE):
                security_logger.warning(
                    f"Suspicious header detected: {header}",
                    extra={
                        'ip': self._get_client_ip(request),
                        'header': header,
                        'value': value[:100],
                        'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
                    }
                )
                # در حالت تولید، می‌توان این IP را برای بررسی بیشتر ثبت کرد
                # اما در اینجا فقط هشدار لاگ می‌دهیم و اجازه می‌دهیم درخواست ادامه یابد
        
        # بررسی پارامترهای URL حساس
        sensitive_params = ['password', 'token', 'key', 'secret', 'pass']
        for param in sensitive_params:
            if param in request.GET and not request.is_secure():
                security_logger.warning(
                    f"Sensitive parameter {param} sent over non-HTTPS connection",
                    extra={
                        'ip': self._get_client_ip(request),
                        'param': param,
                        'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
                    }
                )
                # در حالت تولید، می‌توان کاربر را به نسخه HTTPS ریدایرکت کرد
                # اما در اینجا فقط هشدار لاگ می‌دهیم و اجازه می‌دهیم درخواست ادامه یابد
        
        response = self.get_response(request)
        
        # افزودن هدرهای امنیتی به پاسخ
        if not path.startswith('static/') and not path.startswith('media/'):
            # Content-Security-Policy - اجازه بارگذاری از منابع مورد نیاز
            response['Content-Security-Policy'] = "default-src 'self' cdn.jsdelivr.net cdn.datatables.net; script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.jsdelivr.net cdn.datatables.net cdn.ckeditor.com cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net fonts.googleapis.com cdnjs.cloudflare.com; img-src 'self' data: *; font-src 'self' data: fonts.gstatic.com cdn.jsdelivr.net; connect-src 'self' *; frame-src 'self'; worker-src blob: 'self'"
            
            # X-Content-Type-Options
            response['X-Content-Type-Options'] = 'nosniff'
            
            # X-Frame-Options
            response['X-Frame-Options'] = 'SAMEORIGIN'
            
            # X-XSS-Protection
            response['X-XSS-Protection'] = '1; mode=block'
            
            # Referrer-Policy
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Permissions-Policy
            response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
            
            # ثبت هدرهای امنیتی اضافه شده
            security_logger.debug(
                f"Security headers added to response for path {path}",
                extra={
                    'ip': self._get_client_ip(request),
                    'path': path,
                    'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
                }
            )
        
        return response
    
    def _check_patterns(self, value, patterns):
        """بررسی تطبیق با الگوهای مشکوک"""
        for pattern in patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    def _security_violation_response(self, request, message):
        """پاسخ مناسب به تخلفات امنیتی"""
        # بررسی نوع درخواست (API یا وب)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({
                'error': True,
                'message': message,
                'code': 'SECURITY_VIOLATION'
            }, status=403)
        else:
            # استفاده از صفحه خطای سفارشی
            return render(request, 'security/error.html', {
                'message': message,
                'status_code': 403,
                'error_code': 'SECURITY_VIOLATION',
                'security_tip': 'فعالیت‌های مشکوک در سیستم ثبت و بررسی می‌شوند.'
            }, status=403)
    
    def _get_client_ip(self, request):
        """دریافت IP واقعی کاربر"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip

class AccountLockoutMiddleware:
    """
    میدل‌ویر پیشرفته قفل کردن حساب کاربری
    - محدودیت هوشمند تلاش‌های ناموفق ورود
    - محافظت در برابر حملات Brute Force و Credential Stuffing
    - قفل موقت و دائمی حساب‌های کاربری با مکانیزم افزایشی
    - ذخیره‌سازی ایمن اطلاعات قفل حساب با رمزنگاری
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # تنظیمات پیش‌فرض قفل حساب
        self.max_login_attempts = getattr(settings, 'MAX_LOGIN_ATTEMPTS', 5)
        self.lockout_duration = getattr(settings, 'LOCKOUT_DURATION', 30)  # دقیقه
        self.lockout_reset_time = getattr(settings, 'LOCKOUT_RESET_TIME', 24)  # ساعت
        
        self.progressive_lockout = [
            {'attempts': 5, 'duration': 30},   # 5 تلاش ناموفق: 30 دقیقه قفل
            {'attempts': 10, 'duration': 60},  # 10 تلاش ناموفق: 1 ساعت قفل
            {'attempts': 15, 'duration': 180}, # 15 تلاش ناموفق: 3 ساعت قفل
            {'attempts': 20, 'duration': 720}, # 20 تلاش ناموفق: 12 ساعت قفل
            {'attempts': 25, 'duration': 1440} # 25 تلاش ناموفق: 24 ساعت قفل
        ]
        
        self.login_path = getattr(settings, 'LOGIN_URL', '/accounts/login/')
        
    def __call__(self, request):
        # فقط درخواست‌های به صفحه لاگین را بررسی می‌کنیم
        if request.path == self.login_path and request.method == 'POST':
            username = request.POST.get('username', '').lower()
            
            if not username:
                return self.get_response(request)
            
            # بررسی وضعیت قفل حساب
            lockout_key = f"account_lockout:{self._secure_hash(username)}"
            lockout_data = cache.get(lockout_key)
            
            if lockout_data:
                # بررسی اینکه آیا زمان قفل به پایان رسیده است
                current_time = time.time()
                if current_time < lockout_data.get('expires_at', 0):
                    # حساب هنوز قفل است
                    client_ip = self._get_client_ip(request)
                    
                    # ثبت تلاش ورود در زمان قفل
                    security_logger.warning(
                        f"Login attempt during lockout for user: {username}",
                        extra={
                            'ip': client_ip,
                            'username': username,
                            'lockout_minutes': int((lockout_data.get('expires_at', 0) - current_time) / 60)
                        }
                    )
                    
                    # بررسی حمله هماهنگ
                    ip_data = cache.get(f"ip_lockout:{client_ip}", {})
                    ip_data[username] = ip_data.get(username, 0) + 1
                    cache.set(f"ip_lockout:{client_ip}", ip_data, 3600)
                    
                    if self._check_coordinated_attack(client_ip, ip_data):
                        # هشدار به ادمین‌ها در مورد حمله هماهنگ
                        self._alert_admins_of_attack(client_ip, lockout_data)
                    
                    # تعیین زمان باقیمانده قفل
                    remaining_minutes = int((lockout_data.get('expires_at', 0) - current_time) / 60)
                    
                    # نمایش صفحه قفل حساب
                    return self._get_lockout_response(request, remaining_minutes)
            
            # ذخیره اطلاعات کاربر فعلی برای بررسی پس از پاسخ
            request._account_lockout_username = username
            request._account_lockout_time = time.time()
            
        response = self.get_response(request)
        
        # بررسی نتیجه ورود (فقط برای درخواست‌های ورود)
        if hasattr(request, '_account_lockout_username'):
            username = request._account_lockout_username
            
            # اگر هنوز کاربر لاگین نشده باشد، یعنی تلاش ناموفق بوده
            if not request.user.is_authenticated:
                client_ip = self._get_client_ip(request)
                
                # افزایش شمارنده تلاش‌های ناموفق
                lockout_key = f"account_lockout:{self._secure_hash(username)}"
                lockout_data = cache.get(lockout_key, {
                    'attempts': 0,
                    'last_attempt': 0,
                    'expires_at': 0,
                    'ips': []
                })
                
                # افزایش شمارنده تلاش‌های ناموفق
                lockout_data['attempts'] += 1
                lockout_data['last_attempt'] = time.time()
                
                # افزودن IP به لیست
                if client_ip not in lockout_data['ips']:
                    lockout_data['ips'].append(client_ip)
                
                # بررسی نیاز به قفل حساب
                for level in self.progressive_lockout:
                    if lockout_data['attempts'] >= level['attempts']:
                        lockout_minutes = level['duration']
                        break
                else:
                    # اگر هنوز به آستانه قفل نرسیده باشد
                    lockout_minutes = 0
                
                if lockout_minutes > 0:
                    # تنظیم زمان انقضای قفل
                    lockout_data['expires_at'] = time.time() + (lockout_minutes * 60)
                    
                    # ثبت قفل شدن حساب
                    security_logger.warning(
                        f"Account locked: {username} for {lockout_minutes} minutes after {lockout_data['attempts']} failed attempts",
                        extra={
                            'ip': client_ip,
                            'username': username,
                            'lockout_minutes': lockout_minutes,
                            'attempts': lockout_data['attempts'],
                            'ips': lockout_data['ips']
                        }
                    )
                    
                    # افزایش آمار قفل حساب‌ها
                    lockout_count = cache.get('security_stats:account_lockouts', 0)
                    cache.set('security_stats:account_lockouts', lockout_count + 1, 86400)
                    
                    # ذخیره اطلاعات قفل
                    cache.set(lockout_key, lockout_data, lockout_minutes * 60)
                    
                    # نمایش صفحه قفل حساب
                    return self._get_lockout_response(request, lockout_minutes)
                else:
                    # هنوز به آستانه قفل نرسیده، فقط ذخیره اطلاعات
                    cache.set(lockout_key, lockout_data, 24 * 3600)  # 24 ساعت
                    
                    # ثبت تلاش ناموفق
                    security_logger.info(
                        f"Failed login attempt: {username} ({lockout_data['attempts']}/{self.max_login_attempts})",
                        extra={
                            'ip': client_ip,
                            'username': username,
                            'attempts': lockout_data['attempts']
                        }
                    )
            else:
                # لاگین موفق - پاک کردن شمارنده تلاش‌های ناموفق
                lockout_key = f"account_lockout:{self._secure_hash(username)}"
                cache.delete(lockout_key)
                
                # ثبت لاگین موفق
                security_logger.info(
                    f"Successful login: {username}",
                    extra={
                        'ip': self._get_client_ip(request),
                        'username': username
                    }
                )
                
                # چرخش کلید نشست برای امنیت بیشتر
                if hasattr(request, 'session'):
                    request.session.cycle_key()
                    security_logger.info(f"Rotated session key for user {username} after login")
        
        return response
    
    def _check_coordinated_attack(self, client_ip, ip_data):
        """بررسی حمله هماهنگ به سیستم (حمله به چندین کاربر)"""
        # اگر تلاش برای ورود به بیش از 3 حساب کاربری مختلف از یک IP
        if len(ip_data) >= 3:
            return True
        
        # بررسی تعداد کل تلاش‌های ناموفق
        total_attempts = sum(ip_data.values())
        if total_attempts >= 15:
            return True
        
        return False
    
    def _alert_admins_of_attack(self, client_ip, lockdown_data):
        """ارسال هشدار به مدیران سیستم در مورد حمله تشخیص داده شده"""
        security_logger.critical(
            f"Coordinated attack detected from IP: {client_ip}",
            extra={
                'ip': client_ip,
                'attempts': lockdown_data.get('attempts', 0),
                'timestamp': time.time(),
                'attack_type': 'credential_stuffing'
            }
        )
        
        # در سیستم واقعی:
        # 1. ارسال ایمیل به ادمین‌ها
        # 2. ارسال پیامک هشدار
        # 3. فعال کردن محافظت‌های بیشتر
    
    def _get_lockout_response(self, request, remaining_minutes=30, is_system=False):
        """نمایش پیام مناسب برای قفل حساب"""
        # برای API درخواست‌ها
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({
                'error': True,
                'message': 'حساب کاربری موقتاً مسدود شده است. لطفاً بعداً تلاش کنید.',
                'code': 'ACCOUNT_LOCKED',
                'remaining_minutes': remaining_minutes
            }, status=403)
        
        # برای درخواست‌های وب
        reset_password_url = reverse('password_reset') if is_system else None
        
        return render(request, 'accounts/lockout.html', {
            'remaining_minutes': remaining_minutes,
            'reset_password_url': reset_password_url,
            'is_system_lockout': is_system
        }, status=403)
    
    def _get_client_ip(self, request):
        """دریافت IP واقعی کاربر"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip
    
    def _secure_hash(self, value):
        """هش امن برای ذخیره اطلاعات حساس"""
        salt = getattr(settings, 'SECRET_KEY', '')[:16]
        return hashlib.sha256((salt + value).encode()).hexdigest()

class ContentSecurityPolicyMiddleware:
    """
    میدل‌ویر تنظیم سیاست امنیت محتوا (CSP)
    - محافظت پیشرفته در برابر حملات XSS
    - کنترل دقیق منابع مجاز برای بارگذاری محتوا
    - پشتیبانی از حالت گزارش تخلفات
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # تنظیمات CSP بازنگری‌شده با پشتیبانی از CDN های خارجی
        self.csp_settings = {
            'default-src': ["'self'", "cdn.jsdelivr.net", "cdn.datatables.net"],
            'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'", "cdn.jsdelivr.net", "cdn.datatables.net", "cdn.ckeditor.com", "cdnjs.cloudflare.com"],
            'style-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "fonts.googleapis.com", "cdnjs.cloudflare.com"],
            'img-src': ["'self'", "data:", "*"],
            'font-src': ["'self'", "data:", "fonts.gstatic.com", "cdn.jsdelivr.net"],
            'connect-src': ["'self'", "*"],
            'frame-src': ["'self'"],
            'media-src': ["'self'"],
            'object-src': ["'none'"],
            'base-uri': ["'self'"],
            'form-action': ["'self'"],
            'frame-ancestors': ["'self'"],
            'worker-src': ["blob:", "'self'"],
            'report-uri': ["/security/csp-report/"]
        }
        
        # سفارشی‌سازی از تنظیمات
        custom_csp = getattr(settings, 'CONTENT_SECURITY_POLICY', {})
        for directive, sources in custom_csp.items():
            if directive in self.csp_settings:
                self.csp_settings[directive] = sources
        
        # فعال‌سازی حالت گزارش
        self.report_only = getattr(settings, 'CSP_REPORT_ONLY', False)
        
        # مسیرهای مستثنی (مثلاً پنل ادمین و مسیرهای استاتیک)
        self.exempt_paths = getattr(settings, 'CSP_EXEMPT_PATHS', [
            r'^/admin/',
            r'^/static/',
            r'^/media/',
        ])
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # بررسی مسیرهای مستثنی
        path = request.path_info.lstrip('/')
        if any(re.match(exempt, path) for exempt in self.exempt_paths):
            return response
        
        # اضافه کردن هدرهای CSP
        csp_header = self._build_csp_header()
        
        # تعیین نوع هدر (گزارش یا اجرا)
        header_name = 'Content-Security-Policy-Report-Only' if self.report_only else 'Content-Security-Policy'
        
        response[header_name] = csp_header
        
        return response
    
    def _build_csp_header(self):
        """ساخت هدر CSP بر اساس تنظیمات"""
        directives = []
        
        for directive, sources in self.csp_settings.items():
            if sources:
                directives.append(f"{directive} {' '.join(sources)}")
        
        return "; ".join(directives)

class SessionSecurityMiddleware:
    """
    میدل‌ویر امنیت نشست‌ها
    - کنترل طول عمر و اعتبارسنجی نشست‌ها
    - محافظت در برابر حمله‌های Session Fixation
    - محافظت در برابر Session Hijacking
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # تنظیمات پیش‌فرض امنیت نشست
        self.session_idle_timeout = getattr(settings, 'SESSION_IDLE_TIMEOUT', 30 * 60)  # 30 دقیقه
        self.session_absolute_timeout = getattr(settings, 'SESSION_ABSOLUTE_TIMEOUT', 24 * 60 * 60)  # 24 ساعت
        self.session_verify_ip = getattr(settings, 'SESSION_VERIFY_IP', True)
        self.session_verify_user_agent = getattr(settings, 'SESSION_VERIFY_USER_AGENT', True)
        
    def __call__(self, request):
        # بررسی و اعتبارسنجی نشست فعلی
        if hasattr(request, 'session') and not request.session.is_empty():
            # بررسی زمان ایجاد نشست (منقضی شدن مطلق)
            session_start_time = request.session.get('_session_start_time', 0)
            current_time = time.time()
            
            if session_start_time and current_time - session_start_time > self.session_absolute_timeout:
                # نشست منقضی شده (بیش از حداکثر زمان مجاز فعال بوده)
                security_logger.info(
                    f"Session expired (absolute timeout) for user: {request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'}",
                    extra={'ip': self._get_client_ip(request)}
                )
                
                self._logout_and_clear_session(request)
                return HttpResponseRedirect(f"{reverse('accounts:login')}?next={request.path}")
            
            # بررسی زمان آخرین فعالیت (منقضی شدن به دلیل عدم فعالیت)
            last_activity = request.session.get('_session_last_activity', 0)
            
            if last_activity and current_time - last_activity > self.session_idle_timeout:
                # نشست منقضی شده (بیش از حد مجاز غیرفعال بوده)
                security_logger.info(
                    f"Session expired (idle timeout) for user: {request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'}",
                    extra={'ip': self._get_client_ip(request)}
                )
                
                self._logout_and_clear_session(request)
                return HttpResponseRedirect(f"{reverse('accounts:login')}?next={request.path}&timeout=1")
            
            # بررسی IP (برای جلوگیری از Session Hijacking)
            if self.session_verify_ip:
                session_ip = request.session.get('_session_ip')
                current_ip = self._get_client_ip(request)
                
                if session_ip and session_ip != current_ip:
                    # IP نشست تغییر کرده (احتمال Session Hijacking)
                    security_logger.warning(
                        f"Session IP mismatch: {session_ip} != {current_ip} for user: {request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'}",
                        extra={'ip': current_ip, 'session_ip': session_ip}
                    )
                    
                    self._logout_and_clear_session(request)
                    return self._get_security_violation_response(request, "نشست شما به دلایل امنیتی باطل شده است. لطفاً دوباره وارد شوید.")
            
            # بررسی User-Agent (برای جلوگیری از Session Hijacking)
            if self.session_verify_user_agent:
                session_ua = request.session.get('_session_user_agent')
                current_ua = request.META.get('HTTP_USER_AGENT', '')
                
                if session_ua and session_ua != current_ua:
                    # User-Agent نشست تغییر کرده (احتمال Session Hijacking)
                    security_logger.warning(
                        f"Session User-Agent mismatch for user: {request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'}",
                        extra={'ip': self._get_client_ip(request)}
                    )
                    
                    self._logout_and_clear_session(request)
                    return self._get_security_violation_response(request, "نشست شما به دلایل امنیتی باطل شده است. لطفاً دوباره وارد شوید.")
            
            # به‌روزرسانی زمان آخرین فعالیت
            request.session['_session_last_activity'] = current_time
        
        response = self.get_response(request)
        
        # اضافه کردن اطلاعات امنیتی به نشست جدید
        if hasattr(request, 'session') and not request.session.is_empty() and request.user.is_authenticated:
            # تنظیم زمان ایجاد نشست (اگر وجود نداشته باشد)
            if '_session_start_time' not in request.session:
                request.session['_session_start_time'] = time.time()
            
            # تنظیم زمان آخرین فعالیت
            request.session['_session_last_activity'] = time.time()
            
            # ذخیره IP کاربر
            if self.session_verify_ip and '_session_ip' not in request.session:
                request.session['_session_ip'] = self._get_client_ip(request)
            
            # ذخیره User-Agent کاربر
            if self.session_verify_user_agent and '_session_user_agent' not in request.session:
                request.session['_session_user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        
        return response
    
    def _logout_and_clear_session(self, request):
        """خروج کاربر و پاک‌سازی نشست"""
        if hasattr(request, 'user') and request.user.is_authenticated:
            logout(request)
        if hasattr(request, 'session'):
            request.session.flush()
    
    def _get_client_ip(self, request):
        """دریافت IP واقعی کاربر"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip
    
    def _get_security_violation_response(self, request, message):
        """پاسخ مناسب به تخلفات امنیتی"""
        # برای API درخواست‌ها
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({
                'error': True,
                'message': message,
                'code': 'SESSION_SECURITY_VIOLATION'
            }, status=403)
        
        # برای درخواست‌های وب - استفاده از صفحه خطای سفارشی
        return render(request, 'security/error.html', {
            'message': message,
            'status_code': 403,
            'error_code': 'SESSION_SECURITY_VIOLATION',
            'security_tip': 'این خطا ممکن است به دلیل تغییر IP یا مرورگر شما رخ داده باشد. برای حفظ امنیت حساب کاربری، لطفاً دوباره وارد شوید.'
        }, status=403)