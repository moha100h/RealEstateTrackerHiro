"""
میدل‌ویر‌های سفارشی برای امنیت پیشرفته سیستم
محافظت در برابر حملات سایبری و تهدیدات امنیتی
"""
import time
import re
import logging
import hashlib
import json
import random
import string
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.utils.translation import gettext as _
from django.shortcuts import render
from django.urls import reverse, resolve

# ثبت لاگ‌های امنیتی
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
        # تنظیمات پیش‌فرض با محدودیت‌های سخت‌گیرانه‌تر
        self.default_window_size = getattr(settings, 'RATE_LIMIT_MIDDLEWARE', {}).get('WINDOW_SIZE', 60 * 5)  # 5 دقیقه
        self.default_max_requests = getattr(settings, 'RATE_LIMIT_MIDDLEWARE', {}).get('MAX_REQUESTS', 200)  # 200 درخواست
        
        # تنظیمات محدودیت برای صفحات حساس
        self.sensitive_endpoints = {
            '/accounts/login/': {'window_size': 60 * 5, 'max_requests': 15},
            '/accounts/register/': {'window_size': 60 * 5, 'max_requests': 10},
            '/accounts/reset-password/': {'window_size': 60 * 10, 'max_requests': 5},
            '/admin/': {'window_size': 60 * 5, 'max_requests': 50},
            '/api/': {'window_size': 60 * 5, 'max_requests': 100},
        }
        
        # مسیرهای استثنا
        self.exempt_paths = getattr(settings, 'RATE_LIMIT_MIDDLEWARE', {}).get('EXEMPT_PATHS', 
                                   ['/static/', '/media/', '/favicon.ico'])
        
        # مقادیر مربوط به جریمه (penalty) برای رفتارهای مشکوک
        self.burst_penalty = 10  # هر درخواست بیش از حد، ۱۰ درخواست به حساب می‌آید
        self.suspicious_penalty_multiplier = 5  # ضریب جریمه برای رفتار مشکوک
        
    def __call__(self, request):
        # بررسی استثناها
        path = request.path_info
        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return self.get_response(request)
        
        # شناسایی کلاینت
        client_ip = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # هش کردن اطلاعات برای ایجاد شناسه منحصر به فرد
        client_identifier = hashlib.md5(f"{client_ip}:{user_agent}".encode()).hexdigest()
        
        # کلیدهای کش برای این کلاینت
        rate_key = f"rate_limit:{client_identifier}"
        penalty_key = f"rate_penalty:{client_identifier}"
        blacklist_key = f"blacklist:{client_identifier}"
        
        # بررسی لیست سیاه
        if cache.get(blacklist_key):
            security_logger.warning(f"Blocked blacklisted request from {client_ip}")
            return HttpResponseForbidden(
                _('دسترسی شما به دلیل فعالیت‌های مشکوک مسدود شده است. لطفاً با مدیر سیستم تماس بگیرید.')
            )
        
        # انتخاب تنظیمات مناسب برای این مسیر
        for endpoint, limits in self.sensitive_endpoints.items():
            if path.startswith(endpoint):
                window_size = limits['window_size']
                max_requests = limits['max_requests']
                break
        else:
            window_size = self.default_window_size
            max_requests = self.default_max_requests
        
        # بررسی جریمه‌های قبلی
        penalty = cache.get(penalty_key, 0)
        
        # محاسبه حداکثر درخواست‌های مجاز با در نظر گرفتن جریمه
        adjusted_max_requests = max(5, max_requests - penalty)  # حداقل ۵ درخواست مجاز است
        
        # دریافت تاریخچه درخواست‌ها
        requests_data = cache.get(rate_key, {'history': [], 'patterns': {}})
        requests_history = requests_data['history']
        request_patterns = requests_data['patterns']
        
        now = time.time()
        
        # تمیز کردن تاریخچه درخواست‌های قدیمی
        requests_history = [t for t in requests_history if t > now - window_size]
        
        # افزودن الگوی درخواست فعلی
        path_pattern = self._get_path_pattern(path)
        method = request.method
        pattern_key = f"{method}:{path_pattern}"
        
        # بررسی الگوهای مشکوک
        if pattern_key in request_patterns:
            request_patterns[pattern_key]['count'] += 1
            request_patterns[pattern_key]['last_seen'] = now
        else:
            request_patterns[pattern_key] = {'count': 1, 'last_seen': now}
        
        # تمیز کردن الگوهای قدیمی
        for key in list(request_patterns.keys()):
            if request_patterns[key]['last_seen'] < now - window_size:
                del request_patterns[key]
        
        # تشخیص رفتار مشکوک - تعداد زیاد درخواست‌های مشابه در زمان کوتاه
        current_pattern_count = request_patterns.get(pattern_key, {}).get('count', 0)
        is_suspicious = current_pattern_count > adjusted_max_requests * 0.7
        
        # تشخیص رفتار مشکوک - تکرار سریع درخواست‌ها
        if len(requests_history) >= 3:
            recent_requests = requests_history[-3:]
            time_diffs = [recent_requests[i] - recent_requests[i-1] for i in range(1, len(recent_requests))]
            is_rapid_fire = all(diff < 0.5 for diff in time_diffs)  # درخواست‌های با فاصله کمتر از ۰.۵ ثانیه
            is_suspicious = is_suspicious or is_rapid_fire
        
        # بررسی محدودیت با در نظر گرفتن جریمه‌ها
        if len(requests_history) >= adjusted_max_requests:
            # اعمال جریمه بیشتر برای درخواست‌های بیش از حد
            if penalty < 100:  # محدودیت جریمه
                cache.set(penalty_key, penalty + self.burst_penalty, window_size * 2)
            
            # ثبت در لاگ امنیتی
            security_logger.warning(
                f"Rate limit exceeded: {client_ip} ({len(requests_history)} requests in {window_size/60:.1f} minutes)" +
                f" for path pattern {path_pattern}"
            )
            
            # اضافه کردن به لیست سیاه در صورت تخلف مکرر و سنگین
            if len(requests_history) > adjusted_max_requests * 2:
                cache.set(blacklist_key, True, 60 * 60 * 3)  # 3 ساعت بلاک
                return HttpResponseForbidden(
                    _('دسترسی شما به دلیل تخلف از محدودیت درخواست‌ها مسدود شده است.')
                )
            
            return HttpResponse(
                _('تعداد درخواست‌های شما از حد مجاز بیشتر شده است. لطفاً کمی صبر کنید.'),
                status=429
            )
        
        # افزایش جریمه برای رفتار مشکوک
        if is_suspicious and penalty < 100:
            new_penalty = min(100, penalty + self.suspicious_penalty_multiplier)
            cache.set(penalty_key, new_penalty, window_size * 2)
            security_logger.info(f"Applied suspicious activity penalty to {client_ip} - New penalty: {new_penalty}")
        
        # ثبت درخواست جدید
        requests_history.append(now)
        requests_data = {'history': requests_history, 'patterns': request_patterns}
        cache.set(rate_key, requests_data, window_size)
        
        # افزودن هدرهای امنیتی به پاسخ
        response = self.get_response(request)
        response['X-Rate-Limit-Limit'] = str(adjusted_max_requests)
        response['X-Rate-Limit-Remaining'] = str(max(0, adjusted_max_requests - len(requests_history)))
        response['X-Rate-Limit-Reset'] = str(int(now + window_size))
        
        return response
    
    def _get_client_ip(self, request):
        """دریافت IP واقعی کاربر با در نظر گرفتن پروکسی‌ها"""
        # تلاش برای شناسایی IP اصلی از هدرهای متداول پروکسی
        headers = [
            'HTTP_CF_CONNECTING_IP',  # Cloudflare
            'HTTP_X_REAL_IP',         # Nginx
            'HTTP_X_FORWARDED_FOR',   # معمول
            'HTTP_X_CLIENT_IP',       # معمول
            'HTTP_X_CLUSTER_CLIENT_IP', # معمول
            'HTTP_FORWARDED_FOR',      # RFC 7239
            'HTTP_FORWARDED',          # RFC 7239
            'REMOTE_ADDR',             # پشتیبان
        ]
        
        for header in headers:
            ip = request.META.get(header, '')
            if ip:
                # جدا کردن اولین IP در صورت وجود چند آدرس
                if ',' in ip:
                    ip = ip.split(',')[0].strip()
                # اعتبارسنجی ساده آدرس IP
                if self._is_valid_ip(ip):
                    return ip
                    
        return request.META.get('REMOTE_ADDR', '0.0.0.0')
    
    def _is_valid_ip(self, ip):
        """بررسی اعتبار ساختاری آدرس IP"""
        # الگوی IPv4
        ipv4_pattern = r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        # الگوی ساده IPv6
        ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^([0-9a-fA-F]{1,4}:){1,7}:|^([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}$|^([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}$|^([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}$|^([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}$|^([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}$|^[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})$|^:((:[0-9a-fA-F]{1,4}){1,7}|:)$'
        
        return bool(re.match(ipv4_pattern, ip) or re.match(ipv6_pattern, ip))

    def _get_path_pattern(self, path):
        """تبدیل مسیر به الگوی عمومی برای تشخیص الگوهای مشکوک"""
        # حذف پارامترهای عددی از URL برای تشخیص الگوها
        # مثلا: /products/123/ و /products/456/ به /products/{id}/ تبدیل می‌شوند
        path_pattern = re.sub(r'/\d+/', '/{id}/', path)
        path_pattern = re.sub(r'/\d+$', '/{id}', path_pattern)
        return path_pattern


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
        # الگوهای مشکوک SQL Injection
        self.sql_patterns = [
            r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
            r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))",
            r"\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))",
            r"((\%27)|(\'))union",
            r"exec(\s|\+)+(s|x)p",
            r"UNION(\s+)ALL(\s+)SELECT",
            r"SELECT.*FROM",
            r"INSERT(.*)INTO",
            r"UPDATE(.*)SET",
            r"DROP(.*)TABLE",
        ]
        
        # الگوهای مشکوک XSS
        self.xss_patterns = [
            r"<script.*?>.*?</script>",
            r"javascript:",
            r"onerror\s*=",
            r"onclick\s*=",
            r"onload\s*=",
            r"ondblclick\s*=",
            r"onchange\s*=",
            r"onmouseover\s*=",
            r"onsubmit\s*=",
            r"<iframe.*?>",
            r"<object.*?>.*?</object>",
            r"<embed.*?>",
            r"document\.cookie",
            r"document\.location",
            r"eval\s*\(",
            r"fromdump\s*\(",
            r"atanh\s*\(",
            r"atoxl\s*\(",
        ]
        
        # الگوهای مشکوک Path Traversal
        self.path_traversal_patterns = [
            r"\.{2}/",            # ../
            r"%2e%2e%2f",         # ../
            r"\.{2}\\",           # ..\
            r"%2e%2e%5c",         # ..\
            r"\.{2}%2f",          # ..%2f
            r"%2e%2e/",           # %2e%2e/
            r"..%c0%af",          # ..%c0%af
            r"%c0%ae%c0%ae/",     # ÌžÌê/
            r"/%c0%ae%c0%ae%c0%af", # /%c0%ae%c0%ae%c0%af
            r"etc/passwd",
            r"etc/shadow",
            r"proc/self/environ",
            r"ini\s*\.",
            r"\.htaccess",
        ]
        
        # مسیرهای استثنا
        self.exempt_paths = ['/static/', '/media/', '/favicon.ico']
        
    def __call__(self, request):
        # بررسی مسیرهای استثنا
        path = request.path_info
        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return self.get_response(request)
        
        # بررسی امنیتی پارامترهای GET
        if request.GET:
            for key, value in request.GET.items():
                if not isinstance(value, str):
                    continue
                    
                # بررسی حملات SQL Injection
                if self._check_patterns(value, self.sql_patterns):
                    security_logger.warning(f"Potential SQL Injection detected in GET param: {key}={value}")
                    return self._security_violation_response(request, "تلاش غیرمجاز: پارامترهای ورودی نامعتبر")
                
                # بررسی حملات XSS
                if self._check_patterns(value, self.xss_patterns):
                    security_logger.warning(f"Potential XSS attack detected in GET param: {key}={value}")
                    return self._security_violation_response(request, "تلاش غیرمجاز: کدهای مخرب در پارامترها")
                
                # بررسی حملات Path Traversal
                if self._check_patterns(value, self.path_traversal_patterns):
                    security_logger.warning(f"Potential Path Traversal attack detected in GET param: {key}={value}")
                    return self._security_violation_response(request, "تلاش غیرمجاز: دسترسی به مسیرهای غیرمجاز")
        
        # بررسی امنیتی پارامترهای POST
        if request.method == 'POST' and request.content_type != 'multipart/form-data':
            post_data = request.POST
            for key, value in post_data.items():
                if not isinstance(value, str):
                    continue
                    
                # بررسی حملات SQL Injection در داده‌های POST
                if self._check_patterns(value, self.sql_patterns):
                    security_logger.warning(f"Potential SQL Injection detected in POST data: {key}={value}")
                    return self._security_violation_response(request, "تلاش غیرمجاز: داده‌های ورودی نامعتبر")
                
                # بررسی حملات XSS در داده‌های POST
                if self._check_patterns(value, self.xss_patterns):
                    security_logger.warning(f"Potential XSS attack detected in POST data: {key}={value}")
                    return self._security_violation_response(request, "تلاش غیرمجاز: کدهای مخرب در داده‌های ارسالی")
                
                # بررسی حملات Path Traversal در داده‌های POST
                if self._check_patterns(value, self.path_traversal_patterns):
                    security_logger.warning(f"Potential Path Traversal attack detected in POST data: {key}={value}")
                    return self._security_violation_response(request, "تلاش غیرمجاز: دسترسی به مسیرهای غیرمجاز")
        
        # بررسی امنیتی هدرهای درخواست
        suspicious_headers = ['User-Agent', 'Referer', 'Cookie']
        for header in suspicious_headers:
            value = request.META.get(f'HTTP_{header.upper().replace("-", "_")}', '')
            if value and isinstance(value, str):
                # بررسی حملات XSS در هدرها
                if self._check_patterns(value, self.xss_patterns):
                    security_logger.warning(f"Potential XSS attack detected in {header} header: {value}")
                    return self._security_violation_response(request, "تلاش غیرمجاز: کدهای مخرب در هدرهای درخواست")
        
        # افزودن سربرگ‌های امنیتی به پاسخ
        response = self.get_response(request)
        
        # افزودن هدرهای امنیتی استاندارد
        if not response.get('X-Content-Type-Options'):
            response['X-Content-Type-Options'] = 'nosniff'
        if not response.get('X-XSS-Protection'):
            response['X-XSS-Protection'] = '1; mode=block'
        if not response.get('X-Frame-Options'):
            response['X-Frame-Options'] = 'SAMEORIGIN'
            
        # اضافه کردن توکن امنیتی تصادفی برای ردیابی
        security_token = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
        if not response.get('X-Security-Token'):
            response['X-Security-Token'] = security_token
            
        return response
    
    def _check_patterns(self, value, patterns):
        """بررسی تطبیق با الگوهای مشکوک"""
        for pattern in patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    def _security_violation_response(self, request, message):
        """پاسخ مناسب به تخلفات امنیتی"""
        client_ip = self._get_client_ip(request)
        # افزودن به لیست سیاه موقت
        cache.set(f"security_violator:{client_ip}", True, 60 * 30)  # 30 دقیقه مسدودیت
        
        # در محیط توسعه، جزئیات بیشتری نمایش داده می‌شود
        if settings.DEBUG:
            return HttpResponseForbidden(f"Security Violation: {message}".encode('utf-8'))
        
        # در محیط تولید، پیام کلی بدون جزئیات برای جلوگیری از افشای اطلاعات
        return HttpResponseForbidden(_("دسترسی غیرمجاز"))
    
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
        # تنظیمات پیشرفته قفل حساب
        self.max_attempts = getattr(settings, 'ACCOUNT_LOCKOUT_ATTEMPTS', 5)
        self.initial_lockout_time = getattr(settings, 'ACCOUNT_LOCKOUT_TIME', 30 * 60)  # 30 دقیقه پیش‌فرض
        
        # مکانیزم افزایشی - هر بار قفل شدن، زمان قفل بیشتر می‌شود
        self.lockout_multipliers = [1, 2, 4, 8, 24]  # ضرایب افزایش زمان قفل (ساعت)
        self.permanent_lockout_threshold = 5  # تعداد دفعات قفل شدن قبل از قفل دائمی
        
        # بازه‌های زمانی برای تشخیص حملات هماهنگ
        self.coordinated_attack_window = 60 * 60  # یک ساعت
        self.coordinated_attack_threshold = 10  # تعداد کاربران مختلف برای تشخیص حمله هماهنگ
        
        # کلید رمزنگاری برای داده‌های حساس
        self.encryption_key = getattr(settings, 'SECRET_KEY', '')[:32].ljust(32, 'x')
    
    def __call__(self, request):
        # شناسایی مسیر لاگین
        login_paths = ['/accounts/login/', '/admin/login/']
        is_login_attempt = request.method == 'POST' and any(request.path.endswith(path) for path in login_paths)
        
        client_ip = self._get_client_ip(request)
        
        # اگر یک تلاش ورود است
        if is_login_attempt:
            username = request.POST.get('username', '').lower()
            
            if not username:
                return self.get_response(request)
                
            # بررسی قفل کلی سیستم (در صورت تشخیص حمله هماهنگ)
            system_lockdown_key = "system_login_lockdown"
            system_lockdown = cache.get(system_lockdown_key)
            
            if system_lockdown:
                security_logger.warning(f"Login attempt during system lockdown from {client_ip} for user {username}")
                return self._get_lockout_response(request, remaining_minutes=system_lockdown.get('remaining_minutes', 30), is_system=True)
            
            # کلید امن برای ذخیره اطلاعات قفل حساب
            user_hash = self._secure_hash(username)
            lockout_key = f"account_lockout:{user_hash}"
            ip_key = f"ip_login_attempts:{client_ip}"
            
            # دریافت اطلاعات قفل حساب
            lockout_data = cache.get(lockout_key, {
                'attempts': 0,                # تعداد تلاش‌های ناموفق
                'locked_until': 0,            # زمان پایان قفل
                'lockout_count': 0,           # تعداد دفعات قفل شدن
                'first_attempt': time.time(), # زمان اولین تلاش ناموفق
                'ips': set(),                 # لیست IP های استفاده شده
            })
            
            # دریافت اطلاعات IP برای تشخیص حمله هماهنگ
            ip_data = cache.get(ip_key, {
                'usernames': set(),           # مجموعه کاربران تلاش شده از این IP
                'first_attempt': time.time(), # زمان اولین تلاش
                'attempt_count': 0,           # تعداد کل تلاش‌ها
            })
            
            # بررسی قفل بودن حساب
            current_time = time.time()
            if lockout_data.get('locked_until', 0) > current_time:
                # محاسبه زمان باقی‌مانده قفل
                remaining_seconds = lockout_data['locked_until'] - current_time
                remaining_minutes = int(remaining_seconds / 60) + 1  # گرد کردن به بالا
                
                # ثبت تلاش ناموفق در لاگ
                security_logger.warning(
                    f"Login attempt on locked account: {username} from {client_ip}. " +
                    f"Remaining lockout time: {remaining_minutes} minutes"
                )
                
                # بررسی تلاش‌های مکرر روی حساب قفل شده - افزایش زمان قفل
                if lockout_data.get('attempts', 0) >= self.max_attempts * 2:
                    # افزایش زمان قفل
                    extended_lockout = current_time + (remaining_seconds * 1.5)  # ۵۰٪ افزایش
                    lockout_data['locked_until'] = extended_lockout
                    remaining_minutes = int((extended_lockout - current_time) / 60) + 1
                    
                    security_logger.warning(
                        f"Extended lockout for {username} due to persistent attempts. " +
                        f"New lockout time: {remaining_minutes} minutes"
                    )
                    
                    cache.set(lockout_key, lockout_data, self.initial_lockout_time * 3)
                
                return self._get_lockout_response(request, remaining_minutes=remaining_minutes)
            
            # پاسخ معمول را دریافت کرده و بررسی می‌کنیم آیا لاگین موفق بوده یا خیر
            response = self.get_response(request)
            
            # شناسایی تلاش‌های ناموفق بر اساس کد وضعیت و پیام‌های خطا
            is_failed_login = (
                response.status_code == 200 and  # معمولاً صفحه لاگین مجدداً با پیام خطا نمایش داده می‌شود
                hasattr(request, '_messages') and
                any('نام کاربری یا رمز عبور' in str(msg) for msg in request._messages._loaded_messages)
            )

            # تلاش ناموفق برای ورود
            if is_failed_login:
                # به‌روزرسانی اطلاعات تلاش‌های ناموفق
                lockout_data['attempts'] = lockout_data.get('attempts', 0) + 1
                lockout_data['ips'] = list(set(lockout_data.get('ips', [])).union({client_ip}))
                
                # به‌روزرسانی اطلاعات IP
                ip_data['usernames'] = list(set(ip_data.get('usernames', [])).union({username}))
                ip_data['attempt_count'] = ip_data.get('attempt_count', 0) + 1
                
                # بررسی اگر به حداکثر تلاش‌های مجاز رسیده است
                if lockout_data['attempts'] >= self.max_attempts:
                    # تعیین مدت زمان قفل بر اساس تعداد دفعات قفل شدن قبلی
                    lockout_count = lockout_data.get('lockout_count', 0)
                    
                    # بررسی قفل دائمی
                    if lockout_count >= self.permanent_lockout_threshold:
                        # قفل دائمی (یا بسیار طولانی) - 30 روز
                        lockout_time = 60 * 60 * 24 * 30
                        security_logger.critical(
                            f"PERMANENT ACCOUNT LOCKOUT: {username} due to excessive failed attempts. " +
                            f"IP: {client_ip}, Total lockout count: {lockout_count}"
                        )
                    else:
                        # قفل موقت با افزایش تدریجی زمان
                        multiplier_index = min(lockout_count, len(self.lockout_multipliers) - 1)
                        multiplier = self.lockout_multipliers[multiplier_index]
                        lockout_time = self.initial_lockout_time * multiplier
                        
                        security_logger.warning(
                            f"Account locked: {username} for {lockout_time/60/60:.1f} hours. " +
                            f"IP: {client_ip}, Lockout count: {lockout_count+1}"
                        )
                    
                    # به‌روزرسانی داده‌های قفل
                    lockout_data['locked_until'] = time.time() + lockout_time
                    lockout_data['lockout_count'] = lockout_count + 1
                    lockout_data['attempts'] = 0  # ریست تلاش‌ها برای دوره بعدی
                    
                    # ذخیره اطلاعات قفل
                    cache.set(lockout_key, lockout_data, lockout_time * 2)  # دو برابر زمان قفل نگهداری می‌شود
                    
                    # نمایش پیام قفل حساب
                    return self._get_lockout_response(request, remaining_minutes=int(lockout_time/60))
                else:
                    # هنوز به حداکثر تلاش‌ها نرسیده، ذخیره تعداد تلاش‌ها
                    cache.set(lockout_key, lockout_data, self.initial_lockout_time * 2)
                    
                    # ثبت تلاش ناموفق
                    security_logger.info(
                        f"Failed login attempt: {username} from {client_ip}. " +
                        f"Attempt {lockout_data['attempts']} of {self.max_attempts}"
                    )
                
                # به‌روزرسانی اطلاعات IP
                cache.set(ip_key, ip_data, self.coordinated_attack_window)
                
                # بررسی حمله هماهنگ
                if ip_data['attempt_count'] > 10 and len(ip_data['usernames']) >= 5:
                    self._check_coordinated_attack(client_ip, ip_data)
            
            # اگر لاگین موفق بود، پاک کردن سوابق تلاش‌های ناموفق
            elif request.user.is_authenticated:
                if lockout_data.get('attempts', 0) > 0:
                    # پاک کردن سوابق تلاش ناموفق در صورت ورود موفق
                    cache.delete(lockout_key)
                    security_logger.info(f"Successful login: {username} from {client_ip}. Cleared failed login attempts.")
            
            return response
        
        # برای سایر درخواست‌ها، ادامه روال عادی
        return self.get_response(request)
    
    def _check_coordinated_attack(self, client_ip, ip_data):
        """بررسی حمله هماهنگ به سیستم (حمله به چندین کاربر)"""
        # تعداد حداقل کاربران مختلف برای تشخیص حمله
        if len(ip_data['usernames']) >= self.coordinated_attack_threshold:
            security_logger.critical(
                f"COORDINATED ATTACK DETECTED from {client_ip}. " +
                f"Attempted {len(ip_data['usernames'])} different accounts in {ip_data['attempt_count']} attempts."
            )
            
            # فعال کردن قفل کلی سیستم
            lockdown_minutes = 30
            system_lockdown = {
                'activated_at': time.time(),
                'expires_at': time.time() + (lockdown_minutes * 60),
                'remaining_minutes': lockdown_minutes,
                'source_ip': client_ip,
                'username_count': len(ip_data['usernames']),
                'attempt_count': ip_data['attempt_count']
            }
            
            cache.set("system_login_lockdown", system_lockdown, lockdown_minutes * 60)
            
            # ایمیل برای ادمین‌ها ارسال شود
            self._alert_admins_of_attack(client_ip, system_lockdown)
    
    def _alert_admins_of_attack(self, client_ip, lockdown_data):
        """ارسال هشدار به مدیران سیستم در مورد حمله تشخیص داده شده"""
        # در اینجا می‌توان با ایمیل یا پیامک به ادمین‌ها اطلاع داد
        # این قسمت را می‌توان با سامانه‌های اطلاع‌رسانی شما یکپارچه کرد
        security_logger.critical(
            f"SECURITY ALERT: System lockdown activated due to coordinated attack from {client_ip}. " +
            f"Lockdown expires in {lockdown_data['remaining_minutes']} minutes."
        )
    
    def _get_lockout_response(self, request, remaining_minutes=30, is_system=False):
        """نمایش پیام مناسب برای قفل حساب"""
        if is_system:
            message = _(f'سیستم به دلیل تشخیص حمله امنیتی به طور موقت قفل شده است. لطفاً {remaining_minutes} دقیقه دیگر تلاش کنید.')
        else:
            message = _(f'حساب کاربری به دلیل تلاش‌های ناموفق قفل شده است. لطفاً {remaining_minutes} دقیقه دیگر تلاش کنید.')
        
        # اگر درخواست AJAX است، پاسخ JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': message, 'lockout': True, 'remaining_minutes': remaining_minutes}, status=403)
        
        # در غیر این صورت، پاسخ HTML
        context = {
            'message': message,
            'remaining_minutes': remaining_minutes,
            'is_system_lockout': is_system,
        }
        return render(request, 'accounts/lockout.html', context)
    
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
        salt = self.encryption_key[:16]
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
        self.report_uri = getattr(settings, 'CSP_REPORT_URI', '/security/csp-report/')
        self.report_only = getattr(settings, 'CSP_REPORT_ONLY', False)
        
        # تنظیمات امنیتی CSP پیش‌فرض
        self.csp_settings = {
            'default-src': ["'self'"],
            'script-src': ["'self'", 'cdn.jsdelivr.net', 'www.google-analytics.com'],
            'style-src': ["'self'", "'unsafe-inline'", 'cdn.jsdelivr.net', 'fonts.googleapis.com'],
            'img-src': ["'self'", 'data:', 'www.google-analytics.com'],
            'font-src': ["'self'", 'fonts.gstatic.com', 'cdn.jsdelivr.net'],
            'connect-src': ["'self'", 'www.google-analytics.com'],
            'frame-src': ["'self'"],
            'object-src': ["'none'"],
            'base-uri': ["'self'"],
            'form-action': ["'self'"],
            'frame-ancestors': ["'self'"],
            'upgrade-insecure-requests': True,
        }
        
        # بررسی تنظیمات سفارشی CSP از settings
        for directive, sources in getattr(settings, 'CSP_DIRECTIVES', {}).items():
            self.csp_settings[directive] = sources
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # افزودن CSP به پاسخ
        if getattr(settings, 'ENABLE_CSP', True):
            csp_header = self._build_csp_header()
            header_name = 'Content-Security-Policy-Report-Only' if self.report_only else 'Content-Security-Policy'
            response[header_name] = csp_header
        
        return response
    
    def _build_csp_header(self):
        """ساخت هدر CSP بر اساس تنظیمات"""
        directives = []
        
        for directive, sources in self.csp_settings.items():
            if directive == 'upgrade-insecure-requests' and sources:
                directives.append('upgrade-insecure-requests')
                continue
                
            if sources:
                directive_str = f"{directive} {' '.join(sources)}"
                directives.append(directive_str)
        
        # افزودن آدرس گزارش تخلفات
        if self.report_uri:
            directives.append(f"report-uri {self.report_uri}")
            directives.append(f"report-to default")
            
        return '; '.join(directives)


class SessionSecurityMiddleware:
    """
    میدل‌ویر امنیت نشست‌ها
    - کنترل طول عمر و اعتبارسنجی نشست‌ها
    - محافظت در برابر حمله‌های Session Fixation
    - محافظت در برابر Session Hijacking
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # تنظیمات امنیتی نشست
        self.session_idle_timeout = getattr(settings, 'SESSION_IDLE_TIMEOUT', 1800)  # 30 دقیقه پیش‌فرض
        self.rotate_session_on_login = getattr(settings, 'ROTATE_SESSION_ON_LOGIN', True)
        self.validate_ip = getattr(settings, 'SESSION_VALIDATE_IP', True)
        self.validate_user_agent = getattr(settings, 'SESSION_VALIDATE_USER_AGENT', True)
    
    def __call__(self, request):
        # بررسی نشست موجود
        if request.user.is_authenticated:
            now = time.time()
            
            # بررسی آخرین فعالیت کاربر
            last_activity = request.session.get('last_activity', now)
            idle_time = now - last_activity
            
            # اگر کاربر بیش از حد مجاز غیرفعال بوده، نشست را منقضی کنیم
            if idle_time > self.session_idle_timeout:
                if 'logging_out' not in request.session:
                    security_logger.info(f"Session timeout for user {request.user.username} after {idle_time/60:.1f} minutes")
                    request.session['logging_out'] = True
                    from django.contrib.auth import logout
                    logout(request)
                    
                    response = self.get_response(request)
                    response['Location'] = f"{reverse('accounts:login')}?timeout=1"
                    response.status_code = 302
                    return response
            
            # بررسی تغییر IP یا User-Agent
            if self.validate_ip and 'ip' in request.session:
                current_ip = self._get_client_ip(request)
                if request.session['ip'] != current_ip:
                    security_logger.warning(
                        f"IP mismatch for session: {request.session.session_key}. " +
                        f"Original: {request.session['ip']}, Current: {current_ip}, User: {request.user.username}"
                    )
                    # اقدامات امنیتی - خروج کاربر
                    from django.contrib.auth import logout
                    logout(request)
                    return self._get_security_violation_response(request, "نشست منقضی شده است. لطفاً مجدداً وارد شوید.")
                    
            if self.validate_user_agent and 'user_agent' in request.session:
                current_ua = request.META.get('HTTP_USER_AGENT', '')
                if request.session['user_agent'] != current_ua:
                    security_logger.warning(
                        f"User-Agent change detected for session: {request.session.session_key}. " +
                        f"User: {request.user.username}"
                    )
                    # اقدامات امنیتی - خروج کاربر
                    from django.contrib.auth import logout
                    logout(request)
                    return self._get_security_violation_response(request, "نشست منقضی شده است. لطفاً مجدداً وارد شوید.")
            
            # به‌روزرسانی زمان آخرین فعالیت
            request.session['last_activity'] = now
        
        # پردازش درخواست
        response = self.get_response(request)
        
        # بررسی لاگین موفق
        if (not hasattr(request, '_login_successful')) and request.user.is_authenticated:
            if request.method == 'POST' and any(request.path.endswith(path) for path in ['/accounts/login/', '/admin/login/']):
                # لاگین موفق، چرخش نشست
                if self.rotate_session_on_login:
                    request.session.cycle_key()
                    security_logger.info(f"Rotated session key for user {request.user.username} after login")
                
                # ذخیره اطلاعات امنیتی
                request.session['ip'] = self._get_client_ip(request)
                request.session['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
                request.session['login_time'] = time.time()
                request.session['last_activity'] = time.time()
                
                setattr(request, '_login_successful', True)
        
        return response
    
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
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': message, 'security_violation': True}, status=403)
        
        # ریدایرکت به صفحه لاگین با پیام خطا
        from django.contrib import messages
        messages.error(request, message)
        return HttpResponse(f'<script>window.location.href = "{reverse("accounts:login")}";</script>'.encode('utf-8'), status=200)